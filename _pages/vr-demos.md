---
title: BEHAVIOR Dataset of Demos
subtitle: "500 successful human demonstrations in virtual reality"
# description: "TODO(sanjanasrivastava): Add desc"
featured_image: /assets/img/behavior/building.jpg
---

### Imitation learning dataset

The imitation learning dataset is described in the BEHAVIOR documentation. It includes all observation modalities (semantic segmentation, instance segmentation, RGB, depth, highlight), task observations, proprioception, and the action used by the agent. Additionally, each hdf5 contains metadata on the specific task.

To download a single example demonstration (~1 gb):
```bash
wget https://download.cs.stanford.edu/downloads/behavior/bottling_fruit_0_Wainscott_0_int_0_2021-05-24_19-46-46_episode.hdf5
```

To download the entire dataset (~250 gb)
```bash
wget https://download.cs.stanford.edu/downloads/behavior/behavior_imitation_learning_v0.5.0.tar.gz
```

### Virtual reality demonstration

To download the raw hdf5s, which include eyetracking and individual pose of the VR sensors, please use the following command:

To download a single example demonstration (~10 mb):
```bash
https://download.cs.stanford.edu/downloads/behavior/bottling_fruit_0_Wainscott_0_int_0_2021-05-24_19-46-46.hdf5
```

To download the entire dataset (~1.7 gb)
```bash
wget https://download.cs.stanford.edu/downloads/behavior/behavior_virtual_reality_v0.5.0.tar.gz
```
