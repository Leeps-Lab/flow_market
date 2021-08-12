# flow_market

Add to session configs

```
{
    'name': 'flow_market',
    'display_name': 'Flow Market',
    'num_demo_participants': 6,
    'config_file' : 'config.csv',
    'app_sequence': ['flow_market'],
}
```

Function used to send messages from server to client

```
live._live_send_back(self.get_players()[0].participant._session_code, self.get_players()[0].participant._index_in_pages, payloads)
```

payloads is a dictionary mapping of {player_id : data} (see models.py for example use)

```
start postgres server
redis-server

otree resetdb
(for some reason I need to rerun my bash-profile to set the REDIS_URL env var every time I restart my computer..
source ~/.bash-profile
)
otree prodserver 80
```
