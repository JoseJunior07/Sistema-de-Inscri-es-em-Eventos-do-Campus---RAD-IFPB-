# Sistema de Inscrições em Eventos do Campus - RAD (IFPB)

Sistema web para gestão e inscrição em eventos e atividades do campus, desenvolvido com Django para a disciplina de Roteiro de Aprendizagem / Desenvolvimento Web (RAD).

---

## 👥 Integrantes do Grupo
- José Júnior

---

## 🔑 Contas de Teste

| Papel | Usuário | Senha | Finalidade no Teste |
| :--- | :--- | :--- | :--- |
| **Superusuário** | `ifpb` | `ifpb` | Gerenciar Salas no Django Admin |
| **Organizador 1** | `Organizador2` | `rad123` | Criar e gerenciar a *Semana Acadêmica* |
| **Organizador 2** | `Organizador3` | `rad123` | Criar e gerenciar a *Jornada Científica* (teste de isolamento) |
| **Participante 1** | `Participante4` | `rad123` | Testar inscrições e validação de conflito de horário |
| **Participante 2** | `Participante5` | `rad123` | Testar limite e lotação de salas |

---

## 🗺️ Mapa dos Dados de Teste

### 1. Salas Cadastradas
- **Sala 101 (Bloco A)** — Capacidade: 30
- **Sala 102 (Bloco A)** — Capacidade: 30
- **Sala 201 (Bloco B)** — Capacidade: 2 *(Sala reduzida para validação de capacidade máxima)*

### 2. Eventos Cadastrados
- **Semana Acadêmica** (Organizador: `Organizador2`)
- **Jornada Científica** (Organizador: `Organizador3`)

### 3. Atividades e Regras de Negócio Validadas
- **Palestra de Abertura** (*Semana Acadêmica*) | Sala 101 | Conflito de horário bloqueado caso a sala esteja ocupada.
- **Oficina de IA** (*Jornada Científica*) | Sala 102 | Teste de horário concomitante em salas distintas.
- **Minicurso Prático** | Sala 201 (Capacidade: 2) | Bloqueio de inscrição para o 3º participante (Atividade Lotada).

---

## ⚠️ Requisitos Não Implementados
- **Nenhum.** Todos os requisitos funcionais e regras de negócio foram totalmente implementados.
