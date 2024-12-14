# File System Project - Implementation of a Unix/Linux File System
22 Oct 2024
5143 Shell Project
Group Members:
- Brett Mitchell, Sly Rahimi
- Note: P01 and P02 work together (shell interacts with the file system).

## Overview:
- The goal of the project is to create a Unix/Linux style file system managed through an SQLite database, allowing users to execute typical shell commands like ls, cp, mv, and grep. The shell leverages a FastAPI-based API to process user inputs, perform database operations, and handle file management tasks.

## Files:
| File  | Description                  |
|----------|------------------------------|
| create_and_load_db.py | Creates and loads initial information into the database. It includes both string and BLOB values in the contents field. |
| filesystem.db | Stores the information initialized in 'create_and_load_db.py'. |
| sqliteCRUD.py | Interacts with the database through SQL statements to create, read, update, or delete information. |
| api.py | Receives requests from 'shell.py', handling a variety of Linux commands. After receiving a request, it interacts with 'sqliteCRUD.py' to continue carrying out execution of the command. |

## Instructions:
Download all of the files in P01 and P02 and run any of the following commands after populating the database with 'create_and_load_db.py':

## Commands:
| Command  | Description                  | Author   |
|----------|------------------------------|----------|
| `ls`     | List files and directories    | Brett |
| `pwd`    | Print working directory       | Sly |
| `mkdir`  | Make new directory            | Sly |
| `cd, cd .., cd ~`     | Change directory | Brett |
| `mv`      | Move file/directory          | Brett/Sly |
| `cp`      | Copy file/directory          | Brett/Sly |
| `rm`      | Remove file/directory        | Brett |
| `cat`     | Display file(s)              | Brett |
| `less`    | Display file content one screen at a time | Sly |
| `head` | Shows the first few lines of a file | Sly |
| `tail` | Displays the last few lines of a file | Sly |
| `grep` | Searches for patterns within a file | Brett |
| `wc` | Provides word count for a file | Brett |
| `history` | Shows commands previously executed | Brett |
| `!x` | Shows a specific command in history | Sly |
| `chmod` | Change directory/file permissions | Sly/Brett |
| `sort` | Sort contents of a file            | Brett |
| `fortune` | Receive a fortune               | Sly |
| `cowspeak` | Display depiction of a coo    | Sly |
| `man` | Display additional command information | Sly |

## Non-Working Components
- 'pwd' is partially functional, returning the parent ID, but does not provide the name of the parent ID.
- 'mv' worked in all iterations of testing, but gave issues in the live demo/presentation.
