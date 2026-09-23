# Эмулятор командной оболочки

## Общее описание

Консольный эмулятор UNIX-подобной командной оболочки,
реализованный на Python.

На первом этапе реализован интерактивный режим работы,
формирование приглашения на основе данных ОС, раскрытие
переменных окружения, команды-заглушки `ls` и `cd`,
а также команда `exit` и обработка ошибок.

## Структура проекта

* `src/` — исходный код;
* `tests/` — тесты;
* `scripts/` — скрипты для проверки;
* `vfs/` — файлы VFS для следующих этапов;
* `run.sh` — запуск в Linux;
* `run.bat` — запуск в Windows.

## Основные функции

`parse_line()` — разбор команды и раскрытие переменных
окружения.

`build_prompt()` — формирование приглашения вида
`username@hostname:path$`.

`ShellEmulator` — основной класс эмулятора, отвечающий
за обработку команд и работу REPL.

`ls`, `cd` — команды-заглушки текущего этапа.

`exit` — завершение работы программы.

## Настройки

На первом этапе дополнительные параметры запуска
не используются.

## Запуск

Linux:

```bash
./run.sh
```

Windows:

```bat
run.bat
```

Также можно запустить напрямую:

```bash
PYTHONPATH=src python3 -m shell_emulator
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

igor@modern:~$ cd test
cd test

igor@modern:~$ unknown
error: unknown command: unknown

igor@modern:~$ exit
```

Проект выполняется без сторонних библиотек.
