# Meeting Backgrounds

A tool to download and manage meeting background collections.


## Getting started

Clone this repository:
```sh
git clone https://github.com/letmaik/meeting-backgrounds
cd meeting-backgrounds
```

List available background collections:
```sh
$ python meeting-backgrounds.py list

Name: bbc_joy_of_sets
Title: BBC Archive - The joy of sets
Website: https://www.bbc.co.uk/archive/empty_sets_collection/zfvy382
Backgrounds: 96
Downloaded: no
```

Download a background collection for your meeting app:
```sh
$ python meeting-backgrounds.py download --app msteams --bg bbc_joy_of_sets
```
TIP: You can download all collections by leaving out `--bg`.

Remove downloaded backgrounds again:
```sh
$ python meeting-backgrounds.py remove --app msteams --bg bbc_joy_of_sets
```
TIP: You can remove all collections by leaving out `--bg`.

## Supported apps

### Microsoft Teams

- Command line: `--app msteams`
- Operating systems:
  - ✔️ Windows
  - ✔️ macOS (untested)
  - ❌ Linux ([backgrounds not supported yet](https://microsoftteams.uservoice.com/forums/555103-public/suggestions/40247473-background-effects-teams-for-linux))
- Gotchas:
  - After downloading backgrounds, Teams must be restarted.

## Contributions

If you like to help, consider one of the following contributions:
- Addition of more background collections
- Support for more apps

All of the above is easily possible by extending the [`apps.json`](apps.json) and [`backgrounds.json`](backgrounds.json) files.
Your pull request is welcome! :)
