# Meeting Backgrounds

A tool to download and manage meeting background collections.


## Getting started

Clone this repository:
```sh
git clone https://github.com/letmaik/meeting-backgrounds
cd meeting-backgrounds
```

#### List available background collections
```sh
$ python meeting-backgrounds.py list

Name: bbc_joy_of_sets
Title: BBC Archive - The joy of sets
Website: https://www.bbc.co.uk/archive/empty_sets_collection/zfvy382
Backgrounds: 96
Downloaded: no
...
```

#### Download a background collection for your meeting app
```sh
$ python meeting-backgrounds.py download --app msteams --bg bbc_joy_of_sets
```
TIP: You can download all collections by leaving out `--bg`.

#### Remove downloaded backgrounds again
```sh
$ python meeting-backgrounds.py remove --app msteams --bg bbc_joy_of_sets
```
TIP: You can remove all collections by leaving out `--bg`.

#### Open the folder containing downloaded backgrounds
```sh
$ python meeting-backgrounds.py open --app msteams
```

## Background collections

<!-- Re-generate with meeting-backgrounds.py list --markdown -->

Command Line | Title | Backgrounds
-------------|-------|------------
`--bg bbc_joy_of_sets` | [BBC Archive - The joy of sets](https://www.bbc.co.uk/archive/empty_sets_collection/zfvy382) | 96
`--bg pixar` | [Pixar](https://news.disney.com/pixar-video-backgrounds-available) | 13
`--bg dc` | [DC Comics](https://www.dccomics.com/blog/2020/04/01/dial-in-from-the-dc-universe-with-these-virtual-backgrounds) | 20
`--bg fox_animation` | [FOX Animation Domination](https://www.fox.com/animation-domination/download-zoom-backgrounds/) | 10
`--bg starwars` | [Star Wars](https://www.starwars.com/news/star-wars-backgrounds) | 32
`--bg starbucks` | [Starbucks](https://stories.starbucks.com/stories/2020/you-can-still-work-from-starbucks-with-virtual-backgrounds/) | 12
`--bg westelm` | [West Elm](https://blog.westelm.com/2020/03/18/download-these-video-conference-backgrounds-will-let-you-dial-in-from-your-dream-home/) | 34
`--bg hubble` | [Hubble Wallpapers](https://www.spacetelescope.org/images/archive/search/?ranking=80&type=Observation&minimum_size=4&wallpapers=on&sort=-release_date) | 209

## Supported apps

### Microsoft Teams

- Command line: `--app msteams`
- Operating systems:
  - ✔️ Windows
  - ✔️ macOS (untested)
  - ❌ Linux ([backgrounds not supported yet](https://microsoftteams.uservoice.com/forums/555103-public/suggestions/40247473-background-effects-teams-for-linux))
- Gotchas:
  - After downloading backgrounds, Teams must be restarted.
  - On start-up, Teams generates thumbnails for new backgrounds which may take a while.

## Contributions

If you like to help, consider one of the following contributions:
- Addition of more background collections (official sources from copyright holders only)
- Support for more apps

All of the above is easily possible by extending the [`apps.json`](apps.json) and [`backgrounds.json`](backgrounds.json) files.
Your pull request is welcome! :)
