from __future__ import annotations

from collections.abc import Callable, Iterator
from datetime import date, datetime
import sys
from typing import Any

from acd.services.communications_service import MailMessage


class OutlookClassicUnavailableError(RuntimeError):
    """Raised when Outlook Classic COM automation cannot be used."""


class ClassicOutlookMailReader:
    """Read incoming messages from all Outlook Classic stores through COM."""

    OUTLOOK_APPLICATION_PROG_ID = "Outlook.Application"
    OL_FOLDER_INBOX = 6
    OL_MAIL = 43
    PR_SMTP_ADDRESS = "http://schemas.microsoft.com/mapi/proptag/0x39FE001E"

    def __init__(
        self,
        *,
        dispatch: Callable[[str], Any] | None = None,
        co_initialize: Callable[[], None] | None = None,
        co_uninitialize: Callable[[], None] | None = None,
        max_scan: int = 5000,
    ) -> None:
        if max_scan <= 0:
            raise ValueError("max_scan deve ser positivo.")

        self._dispatch = dispatch
        self._co_initialize = co_initialize
        self._co_uninitialize = co_uninitialize
        self._max_scan = max_scan

    def read_from_sender(
        self,
        sender_email: str,
        *,
        since: date | None = None,
        limit: int = 50,
    ) -> tuple[MailMessage, ...]:
        sender = sender_email.strip().casefold()

        if not sender or limit <= 0:
            return ()

        dispatch, co_initialize, co_uninitialize = self._runtime()

        initialized = False

        try:
            co_initialize()
            initialized = True

            outlook = dispatch(self.OUTLOOK_APPLICATION_PROG_ID)
            namespace = outlook.GetNamespace("MAPI")

            results: list[MailMessage] = []
            seen_messages: set[tuple[str, str]] = set()

            for store_id, inbox in self._iter_inboxes(namespace):
                self._read_inbox(
                    inbox=inbox,
                    store_id=store_id,
                    sender=sender,
                    since=since,
                    results=results,
                    seen_messages=seen_messages,
                )

            results.sort(
                key=lambda message: message.received_at,
                reverse=True,
            )

            return tuple(results[:limit])

        except OutlookClassicUnavailableError:
            raise

        except Exception as exc:
            raise OutlookClassicUnavailableError(
                "Não foi possível acessar o Outlook Classic. "
                "Confirme que o Outlook Classic está instalado, possui um perfil "
                "configurado e consegue abrir as Caixas de Entrada."
            ) from exc

        finally:
            if initialized:
                co_uninitialize()

    def _read_inbox(
        self,
        *,
        inbox: Any,
        store_id: str,
        sender: str,
        since: date | None,
        results: list[MailMessage],
        seen_messages: set[tuple[str, str]],
    ) -> None:
        try:
            items = inbox.Items
            items.Sort("[ReceivedTime]", True)
            item_count = int(items.Count)
        except Exception:
            return

        scan_count = min(item_count, self._max_scan)

        for index in range(1, scan_count + 1):
            try:
                item = items.Item(index)
            except Exception:
                continue

            try:
                item_class = int(getattr(item, "Class", 0) or 0)
            except (TypeError, ValueError):
                continue

            if item_class != self.OL_MAIL:
                continue

            received_at = self._received_at(item)

            if received_at is None:
                continue

            if since is not None and received_at.date() < since:
                break

            smtp_sender = self._sender_smtp_address(item)

            if smtp_sender.casefold() != sender:
                continue

            entry_id = str(getattr(item, "EntryID", "") or "").strip()

            message_key = (
                store_id,
                entry_id
                or self._fallback_message_key(
                    smtp_sender,
                    str(getattr(item, "Subject", "") or ""),
                    received_at,
                ),
            )

            if message_key in seen_messages:
                continue

            seen_messages.add(message_key)

            results.append(
                MailMessage(
                    message_id=entry_id,
                    sender_email=smtp_sender,
                    subject=str(getattr(item, "Subject", "") or ""),
                    received_at=received_at,
                    source="outlook_classic",
                )
            )

    def _iter_inboxes(self, namespace: Any) -> Iterator[tuple[str, Any]]:
        yielded = False
        seen_stores: set[str] = set()

        try:
            stores = namespace.Stores
        except Exception:
            stores = None

        if stores is not None:
            for index, store in enumerate(
                self._iter_com_collection(stores),
                start=1,
            ):
                store_id = self._store_id(store, fallback=f"store-{index}")

                if store_id in seen_stores:
                    continue

                try:
                    inbox = store.GetDefaultFolder(self.OL_FOLDER_INBOX)
                except Exception:
                    continue

                if inbox is None:
                    continue

                seen_stores.add(store_id)
                yielded = True

                yield store_id, inbox

        if yielded:
            return

        try:
            inbox = namespace.GetDefaultFolder(self.OL_FOLDER_INBOX)
        except Exception as exc:
            raise OutlookClassicUnavailableError(
                "Não foi possível localizar uma Caixa de Entrada acessível "
                "no perfil do Outlook Classic."
            ) from exc

        if inbox is None:
            raise OutlookClassicUnavailableError(
                "Nenhuma Caixa de Entrada foi encontrada no Outlook Classic."
            )

        yield "default-store", inbox

    @staticmethod
    def _iter_com_collection(collection: Any) -> Iterator[Any]:
        try:
            count = int(collection.Count)
        except Exception:
            count = 0

        if count > 0:
            for index in range(1, count + 1):
                try:
                    yield collection.Item(index)
                except Exception:
                    continue
            return

        try:
            iterator = iter(collection)
        except TypeError:
            return

        yield from iterator

    @staticmethod
    def _store_id(store: Any, *, fallback: str) -> str:
        try:
            store_id = str(getattr(store, "StoreID", "") or "").strip()
        except Exception:
            store_id = ""

        return store_id or fallback

    @staticmethod
    def _fallback_message_key(
        sender_email: str,
        subject: str,
        received_at: datetime,
    ) -> str:
        return "|".join(
            (
                sender_email.casefold(),
                subject.strip(),
                received_at.isoformat(),
            )
        )

    def check_available(self) -> tuple[bool, str]:
        try:
            self.read_from_sender(
                "__acd_probe__@invalid.local",
                limit=1,
            )
        except OutlookClassicUnavailableError as exc:
            return False, str(exc)

        return True, "Outlook Classic detectado e acessível."

    def _runtime(
        self,
    ) -> tuple[
        Callable[[str], Any],
        Callable[[], None],
        Callable[[], None],
    ]:
        if (
            self._dispatch
            and self._co_initialize
            and self._co_uninitialize
        ):
            return (
                self._dispatch,
                self._co_initialize,
                self._co_uninitialize,
            )

        if sys.platform != "win32":
            raise OutlookClassicUnavailableError(
                "A integração com Outlook Classic está disponível apenas no Windows."
            )

        try:
            import pythoncom
            from win32com.client import Dispatch
        except ImportError as exc:
            raise OutlookClassicUnavailableError(
                "A integração com Outlook Classic requer o pacote pywin32."
            ) from exc

        return (
            self._dispatch or Dispatch,
            self._co_initialize or pythoncom.CoInitialize,
            self._co_uninitialize or pythoncom.CoUninitialize,
        )

    @classmethod
    def _sender_smtp_address(cls, item: Any) -> str:
        email_type = str(
            getattr(item, "SenderEmailType", "") or ""
        ).upper()

        if email_type != "EX":
            return str(
                getattr(item, "SenderEmailAddress", "") or ""
            ).strip()

        sender = getattr(item, "Sender", None)

        if sender is None:
            return ""

        try:
            exchange_user = sender.GetExchangeUser()
        except Exception:
            exchange_user = None

        if exchange_user is not None:
            smtp = str(
                getattr(exchange_user, "PrimarySmtpAddress", "") or ""
            ).strip()

            if smtp:
                return smtp

        try:
            return str(
                sender.PropertyAccessor.GetProperty(
                    cls.PR_SMTP_ADDRESS
                )
                or ""
            ).strip()
        except Exception:
            return ""

    @staticmethod
    def _received_at(item: Any) -> datetime | None:
        value = getattr(item, "ReceivedTime", None)

        if not isinstance(value, datetime):
            return None

        if value.tzinfo is not None:
            return value.replace(tzinfo=None)

        return value