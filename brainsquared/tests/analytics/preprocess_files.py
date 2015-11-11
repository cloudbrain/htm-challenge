# from eeg_preprocessing import preprocess_stft_file, write_arrs_to_files

arrs, tagd = preprocess_stft_file('/home/pierre/research/bci/brain_squared/test/test_2.csv', {
    "left": {"main":"channel_3", "artifact":["channel_0", "channel_4", "channel_6"] },
    "right": {"main":"channel_5", "artifact":["channel_2", "channel_4", "channel_7" ] },
})

for k, v in arrs.items():
    arrs[k] = v[tagd != '0.0']

tagd = tagd[tagd != '0.0']

write_arrs_to_files('/home/pierre/research/bci/brain_squared/test', arrs, tagd)

