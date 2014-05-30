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
