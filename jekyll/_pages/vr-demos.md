---
title: BEHAVIOR-100 VR Human Demonstration Dataset
subtitle: "500 successful human demonstrations in virtual reality"
# description: "TODO(sanjanasrivastava): Add desc"
featured_image: /assets/img/behavior/building.jpg
---

BEHAVIOR-100 includes a dataset of 500 VR demonstrations. Each BEHAVIOR-100 activity is demonstrated five times: three times in the same scene and instantiation, showing variation from execution; once in the same scene with a different instantiation; and once in a different scene. Demonstrators in VR have embodiment identical to one of BEHAVIOR-100's embodiments


### Virtual reality demonstration dataset (VR_demos)

This processed dataset could be useful for imitation learning dataset, as described in the BEHAVIOR documentation. It includes all observation modalities (semantic segmentation, instance segmentation, RGB, depth, highlight), task observations, proprioception, and the action used by the agent. Additionally, each hdf5 contains metadata on the specific task.

To download a single example demonstration (~1 gb):
```bash
wget https://download.cs.stanford.edu/downloads/behavior/bottling_fruit_0_Wainscott_0_int_0_2021-05-24_19-46-46_episode.hdf5
```

To download the entire dataset (~250 gb)
```bash
wget https://download.cs.stanford.edu/downloads/behavior/behavior_imitation_learning_v0.5.0.tar.gz
```

### Raw virtual reality demonstration dataset (VR_demos_raw)

To download the raw hdf5s, which include eyetracking and individual pose of the VR sensors, please use the following command:

To download a single example demonstration (~10 mb):
```bash
https://download.cs.stanford.edu/downloads/behavior/bottling_fruit_0_Wainscott_0_int_0_2021-05-24_19-46-46.hdf5
```

To download the entire dataset (~1.7 gb)
```bash
wget https://download.cs.stanford.edu/downloads/behavior/behavior_virtual_reality_v0.5.0.tar.gz
```
