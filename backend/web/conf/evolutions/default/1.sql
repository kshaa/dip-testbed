# --- !Ups

-- # tables

-- user
create table "user" (
  "uuid" uuid not null primary key,
  "username" varchar(255) not null unique
);

-- hardware
create table "hardware" (
  "uuid" uuid not null primary key,
  "type" varchar(255) not null,
  "battery_percent" decimal null
);

create table "hardware_debug_message" (
  "uuid" uuid not null primary key,
  "hardware_uuid" uuid not null,
  "type" varchar(255) not null,
  "message" text null
);

-- disk golf
create table "disk_golf_track" (
  "uuid" uuid not null primary key,
  "owner_uuid" uuid not null,
  "name" varchar(255) not null,
  "timezone" varchar(255) not null
);

create table "disk_golf_basket" (
  "uuid" uuid not null primary key,
  "track_uuid" uuid not null,
  "order_number" int not null,
  "hardware_uuid" uuid null
);

create table "disk_golf_disk" (
  "uuid" uuid not null primary key,
  "track_uuid" uuid not null,
  "hardware_uuid" uuid null
);

create table "disk_golf_game" (
  "uuid" uuid not null primary key,
  "disk_uuid" uuid not null,
  "player_uuid" uuid not null
);

create table "disk_golf_game_stage" (
  "uuid" uuid not null primary key,
  "game_uuid" uuid not null,
  "finish_basket_uuid" uuid not null,
  "timestamp" timestamp with time zone not null,
  "throw_count" int not null
);

-- # constraints

-- hardware
alter table "hardware_debug_message"
  add constraint "fk_hardware_debug_message_hardware_uuid"
  foreign key ("hardware_uuid") references "hardware"("uuid")
  on delete cascade;

-- disk golf
alter table "disk_golf_track"
  add constraint "fk_disk_golf_track_owner_uuid"
  foreign key ("owner_uuid") references "user"("uuid")
  on delete cascade;

alter table "disk_golf_basket"
  add constraint "fk_disk_golf_basket_track_uuid"
  foreign key ("track_uuid") references "disk_golf_track"("uuid")
  on delete cascade;

alter table "disk_golf_basket"
  add constraint "fk_disk_golf_basket_hardware_uuid"
  foreign key ("hardware_uuid") references "hardware"("uuid")
  on delete cascade;

alter table "disk_golf_disk"
  add constraint "fk_disk_golf_disk_track_uuid"
  foreign key ("track_uuid") references "disk_golf_track"("uuid")
  on delete cascade;

alter table "disk_golf_disk"
  add constraint "fk_disk_golf_disk_hardware_uuid"
  foreign key ("hardware_uuid") references "hardware"("uuid")
  on delete cascade;

alter table "disk_golf_game"
  add constraint "fk_disk_golf_game_disk_uuid"
  foreign key ("disk_uuid") references "disk_golf_disk"("uuid")
  on delete cascade;

alter table "disk_golf_game"
  add constraint "fk_disk_golf_game_player_uuid"
  foreign key ("player_uuid") references "user"("uuid")
  on delete cascade;

alter table "disk_golf_game_stage"
  add constraint "fk_disk_golf_game_stage_game_uuid"
  foreign key ("game_uuid") references "disk_golf_game"("uuid")
  on delete cascade;

alter table "disk_golf_game_stage"
  add constraint "fk_disk_golf_game_stage_finish_basket_uuid"
  foreign key ("finish_basket_uuid") references "disk_golf_basket"("uuid")
  on delete cascade;

# --- !Downs

-- # constraints

-- hardware
alter table "hardware_debug_message" drop constraint "fk_hardware_debug_message_hardware_uuid";

-- disk golf
alter table "disk_golf_track" drop constraint "fk_disk_golf_track_owner_uuid";
alter table "disk_golf_basket" drop constraint "fk_disk_golf_basket_track_uuid";
alter table "disk_golf_basket" drop constraint "fk_disk_golf_basket_hardware_uuid";
alter table "disk_golf_disk" drop constraint "fk_disk_golf_disk_track_uuid";
alter table "disk_golf_disk" drop constraint "fk_disk_golf_disk_hardware_uuid";
alter table "disk_golf_game" drop constraint "fk_disk_golf_game_disk_uuid";
alter table "disk_golf_game" drop constraint "fk_disk_golf_game_player_uuid";
alter table "disk_golf_game_stage" drop constraint "fk_disk_golf_game_stage_game_uuid";
alter table "disk_golf_game_stage" drop constraint "fk_disk_golf_game_stage_finish_basket_uuid";

-- # tables

-- user
drop table if exists "user";

-- hardware
drop table if exists "hardware";
drop table if exists "hardware_debug_message";

-- disk golf
drop table if exists "disk_golf_track";
drop table if exists "disk_golf_basket";
drop table if exists "disk_golf_disk";
drop table if exists "disk_golf_game";
drop table if exists "disk_golf_game_stage";
