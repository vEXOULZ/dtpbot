# DTP bot

help

## Set Up

### create twitch token using Twitch CLI

``` bash
twitch token -s "chat:edit chat:read user:write:chat user:read:chat moderator:manage:banned_users user:manage:whispers channel:manage:broadcast user:read:follows moderator:read:followers user:manage:chat_color" -u
```

### environment

copy `environment.yaml.example` to `environment.yaml` and insert redis  url and login information


Redis url format example:
`redis://localhost:6379`
or
`redis://user:pass@localhost:6379`

### redis variables initial setup example

on the redis CLI:

``` sql
SET client_id 'abcdefghijklmnopqrstuvwxyz0123'
SET client_secret 'abcdefghijklmnopqrstuvwxyz0123'
SET token 'abcdefghijklmnopqrstuvwxyz0123'
SET refresh_token 'abcdefghijklmnopqrstuvwxyz0123456789abcdefghijklmn'
```