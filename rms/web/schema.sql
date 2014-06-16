drop table if exists hosts;
create table hosts (
  id integer primary key autoincrement,
  name string not null,
  ip string not null,
  port int not null,
  username string not null,
  password string not null,
  workdir string not null
);
CREATE UNIQUE INDEX name_idx ON `hosts`(`name`);

drop table if exists content;
create table content (
  id integer primary key autoincrement,
  host_id integer not null,
  name string not null
);
CREATE UNIQUE INDEX host_name_idx ON `content`(`host_id`,`name`);
CREATE INDEX contentname_idx ON `content`(`name`);

