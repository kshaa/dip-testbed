# --- !Ups

-- # tables

-- user
create table "user" (
  "uuid" uuid not null primary key,
  "username" varchar(255) not null unique,
  "hashed_password" varchar(512) not null
);

-- hardware
create table "hardware" (
  "uuid" uuid not null primary key,
  "name" varchar(255) not null,
  "owner_uuid" uuid not null
);

create table "hardware_message" (
  "uuid" uuid not null primary key,
  "hardware_uuid" uuid not null,
  "type" varchar(255) not null,
  "message" text not null
);

-- software
create table "software" (
  "uuid" uuid not null primary key,
  "owner_uuid" uuid not null,
  "name" varchar(255) not null,
  "content" bytea not null
);

-- # constraints

-- hardware
alter table "hardware"
  add constraint "fk_hardware_owner_uuid"
  foreign key ("owner_uuid") references "user"("uuid")
  on delete cascade;

alter table "hardware_message"
  add constraint "fk_hardware_message_hardware_uuid"
  foreign key ("hardware_uuid") references "hardware"("uuid")
  on delete cascade;

-- software
alter table "software"
    add constraint "fk_software_owner_uuid"
    foreign key ("owner_uuid") references "user"("uuid")
    on delete cascade;

# --- !Downs

-- # constraints

-- hardware
alter table "hardware" drop constraint "fk_hardware_owner_uuid";
alter table "hardware_message" drop constraint "fk_hardware_message_hardware_uuid";

-- software
alter table "software" drop constraint "fk_software_owner_uuid";

-- # tables

-- user
drop table if exists "user";

-- hardware
drop table if exists "hardware";
drop table if exists "hardware_message";

-- software
drop table if exists "software";
