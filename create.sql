-- Создание таблицы пользователей
CREATE TABLE IF NOT EXISTS Users (
    Id INTEGER PRIMARY KEY,
    Counter INTEGER
);

-- Создание таблицы запросов
CREATE TABLE IF NOT EXISTS SearchResult (
    UserId INTEGER PRIMARY KEY,
    Link TEXT
);
