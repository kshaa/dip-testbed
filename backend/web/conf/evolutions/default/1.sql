# --- !Ups

-- user
create table "user" (
  "uuid" uuid not null primary key,
  "username" varchar(255) not null
);

-- hardware
create table "hardware" (
  "uuid" uuid not null primary key,
  "type" varchar(255) not null,
  "battery_percent" decimal null
);

-- disk golf
create table "disk_golf_track" (
  "uuid" uuid not null primary key,
  "owner_id" bigint not null,
  "name" varchar(255) not null,
  "timezone" varchar(255) not null
);

create table "disk_golf_basket" (
  "uuid" uuid not null primary key,
  "project_uuid" uuid not null,
  "order_number" int not null,
  "hardware_uuid" uuid null
);

create table "disk_golf_disk" (
  "uuid" uuid not null primary key,
  "project_uuid" uuid not null,
  "hardware_uuid" uuid null
);

create table "disk_golf_game" (
  "uuid" uuid not null primary key,
  "project_uuid" uuid not null,
  "disk_golf_disk_uuid" uuid not null,
  "player_id" bigint not null
);

create table "disk_golf_game_throw" (
  "uuid" uuid not null primary key,
  "disk_golf_game_uuid" uuid not null,
  "utc_timestamp" timestamp without time zone not null,
  "disk_golf_basket" uuid not null,
  "throw_count" int not null
);

# --- !Downs

drop table "user" if exists;
drop table "project" if exists;
drop table "hardware" if exists;
drop table "disk_golf_project" if exists;
drop table "disk_golf_basket" if exists;
drop table "disk_golf_disk" if exists;
drop table "disk_golf_game" if exists;
drop table "disk_golf_game_throw" if exists;
