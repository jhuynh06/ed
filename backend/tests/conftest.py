# conftest.py — intentionally minimal
# Note: test_features.py (real librosa/sentence_transformers) and
# test_audio_pipeline_unit.py / test_emotion_fusion.py (stubbed deps)
# must be run in separate invocations due to sys.modules isolation requirements.
#
# Run feature tests:  pytest tests/test_features.py tests/test_workflow.py tests/test_anomaly.py tests/test_bandit.py
# Run pipeline tests: pytest tests/test_audio_pipeline_unit.py tests/test_emotion_fusion.py
