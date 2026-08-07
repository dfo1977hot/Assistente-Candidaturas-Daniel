# ADR-005

## Título

Planner como Bounded Context

---

## Status

Aceito

---

## Contexto

O módulo de planejamento possui responsabilidades distintas do módulo de execução.

---

## Decisão

Criar um domínio exclusivo denominado Planner.

Nenhuma regra de execução será implementada neste módulo.

---

## Consequências

Positivas

- desacoplamento

- facilidade para testes

- evolução independente

Negativas

- maior número de módulos