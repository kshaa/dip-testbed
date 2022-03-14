# --- !Ups

-- # tables

-- hardware
alter table "hardware" add column "is_public" boolean not null default false;

-- software
alter table "software" add column "is_public" boolean not null default false;

-- hardware access
create table "hardware_access" (
  "hardware_uuid" uuid not null,
  "user_uuid" uuid not null
);

-- user
alter table "user" add column "is_manager" boolean not null default false;
alter table "user" add column "is_lab_owner" boolean not null default false;
alter table "user" add column "is_developer" boolean not null default false;

-- # constraints

-- hardware access
alter table "hardware_access"
  add constraint "fk_hardware_access_user_uuid"
  foreign key ("user_uuid") references "user"("uuid")
  on delete cascade;

alter table "hardware_access"
  add constraint "fk_hardware_access_hardware_uuid"
  foreign key ("hardware_uuid") references "hardware"("uuid")
  on delete cascade;

# --- !Downs

-- # constraints

-- hardware access
alter table "hardware_access" drop constraint "fk_hardware_access_user_uuid";
alter table "hardware_access" drop constraint "fk_hardware_access_hardware_uuid";

-- # tables

-- hardware
alter table "hardware" drop column "is_public";

-- software
alter table "software" drop column "is_public";

-- user
alter table "user" drop column "is_manager";
alter table "user" drop column "is_lab_owner";
alter table "user" drop column "is_developer";

-- hardware access
drop table "hardware_access";