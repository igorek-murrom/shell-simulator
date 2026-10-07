# Эмулятор командной оболочки

## Общее описание

Консольный эмулятор UNIX-подобной командной оболочки,
реализованный на Python без сторонних библиотек.

Поддерживается интерактивный режим работы, переменные
окружения, обработка ошибок и стартовые скрипты.

## Структура проекта

* `src/` — исходный код;
* `tests/` — тесты;
* `scripts/` — тестовые сценарии;
* `vfs/` — файлы VFS;
* `run.sh` — запуск в Linux;
* `run.bat` — запуск в Windows.

## Основные функции

`parse_line()` — разбирает команду и раскрывает
переменные окружения.

`build_prompt()` — формирует приглашение вида
`username@hostname:path$`.

`ShellEmulator` — основной класс эмулятора.

`run_interactive()` — запускает интерактивный режим.

`run_script()` — выполняет стартовый скрипт и
останавливается при первой ошибке.

`ls` и `cd` — команды-заглушки первого этапа.

`exit` — завершение работы программы.

## Настройки

Поддерживаются параметры:

```text
--vfs PATH
--script PATH
```

`--vfs` задаёт путь к VFS.

`--script` задаёт стартовый скрипт.

При запуске все заданные параметры выводятся
в отладочном режиме.

На этом этапе VFS ещё не используется для выполнения
команд.

## Стартовый скрипт

Команды записываются по одной на строку.

При выполнении отображаются и введённая команда,
и её вывод.

При первой ошибке выполнение скрипта прекращается.
После сообщения о причине ошибки выводится итоговая строка
`Execution finished with errors.`. В интерактивном режиме эта
строка выводится при завершении сеанса, если возникали ошибки.

## Запуск

Linux:

```bash
./run.sh
```

С параметрами:

```bash
./run.sh \
    --vfs vfs/minimal.json \
    --script scripts/stage2_success.txt
```

Windows:

```bat
run.bat
```

## Тесты

Linux:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Windows:

```bat
set PYTHONPATH=src
py -m unittest discover -s tests -v
```

## Пример

```text
igor@modern:~$ ls
ls

igor@modern:~$ ls $HOME
ls /home/igor

igor@modern:~$ unknown
error: unknown command: unknown

igor@modern:~$ exit
```

Запуск стартового скрипта:

```text
[debug] vfs=vfs/minimal.json
[debug] script=scripts/stage2_success.txt
igor@modern:~$ ls test.txt
ls test.txt
igor@modern:~$ cd folder
cd folder
```
