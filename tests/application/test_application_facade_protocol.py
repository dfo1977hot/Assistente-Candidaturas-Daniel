from typing import assert_type

from acd.application.application_facade import ApplicationFacade
from acd.application.application_facade_protocol import (
    ApplicationFacadeProtocol,
)


def test_application_facade_implements_protocol() -> None:
    facade = ApplicationFacade()

    protocol: ApplicationFacadeProtocol = facade

    assert_type(protocol, ApplicationFacadeProtocol)