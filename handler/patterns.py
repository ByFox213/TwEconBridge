dd_patterns = {
    "trainfngChatRegex": [r'\[.*?]\[chat]: \d+:-?\d+:(.*): (.*)', ""],
    "trainfngJoinRegex": [r'\[.*]\[.*]: \*\*\* \'(.*)\' (.*)', ""],
    "teeworldsChatRegex": [r'\[chat]: \d+:-?\d+:(.*): (.*)', ""],
    "teeworldsLeaveRegex": [r'\[game]: leave player=\'\d+:(.*)\'', "{text_leave}"],
    "teeworldsJoinRegex": [r'\[game]: team_join player=\'\d+:(.*)\' team=0', "{text_join}"],
    "ddnetChatRegex": [r'.* I chat: \d+:-?\d+:(.*): (.*)', ""],
    "ddnetJoinRegex": [r'.* I chat: \*\*\* \'(.*?)\' (.*)', ""]
}
