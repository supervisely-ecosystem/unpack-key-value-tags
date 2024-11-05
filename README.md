<div align="center" markdown> 

<img src="https://user-images.githubusercontent.com/48245050/182631707-5d6a3068-e5fb-45fd-96d4-003d2af90492.png"/>

# Unpack "Key: Value" Tags
  
<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Run">How To Run</a>
</p>

[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack) 
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/unpack-key-value-tags)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/unpack-key-value-tags.png)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/unpack-key-value-tags.png)](https://supervisely.com)

</div>

## Overview 

Application unpacks image and object tags. Unpacking Tag is a simple process that basically just clones original tag and renames it to `key_value` style name.

Example: tag: `fruit` with value: `lemon` will be unpacked as `fruit_lemon` and assigned to the image or object as in original project.

In the modal window you can select whether you want to keep or remove original tags from your objects or images.
Application supports only the following tag value types:
- Any String
- One of String

## How To Run

**Step 1:** Add applicaton to your team from [Ecosystem](https://ecosystem.supervisely.com/apps/unpack-key-value-tags) if it is not there.

**Step 2:** Run application from context menu of project

Go to `Context Menu` -> `Run App` -> `Transform` -> `Unpack key value tags`

<img src="https://i.imgur.com/8d37Ldg.png" width="600"/>

**Step 3:**  Configure options in the modal window

1. Select Tags that should be unpacked
2. Choose whether you want to keep or remove original tags for the result project
3. Type name for the result project 
4. Press `Run` button 

<img src="https://i.imgur.com/ao6ck5z.png" width="400"/>

**Step 4:** Resulting project will be placed to your current Workspace with the chosen name


Watch video guide for more details:

<a data-key="sly-embeded-video-link" href="https://youtu.be/z31-K7NAAbU" data-video-code="z31-K7NAAbU">
    <img src="https://i.imgur.com/TMYoDpu.png" alt="SLY_EMBEDED_VIDEO_LINK"  style="max-width:500px;">
</a>
