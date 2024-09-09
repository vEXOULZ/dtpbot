from core.redis.auths import BotAuths

auths = BotAuths()
auths.client_id     = 'abcdefghijklmnopqrstuvwxyz0123'
auths.client_secret = 'abcdefghijklmnopqrstuvwxyz0123'
auths.token         = 'abcdefghijklmnopqrstuvwxyz0123'
auths.refresh_token = 'abcdefghijklmnopqrstuvwxyz0123456789abcdefghijkl5g'
auths.save()
