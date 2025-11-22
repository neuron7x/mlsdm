from pathlib import Path

from tests.eval.aphasia_eval_suite import AphasiaEvalSuite


def test_aphasia_eval_suite_basic_metrics() -> None:
    corpus_path = Path("tests/eval/aphasia_corpus.json")
    assert corpus_path.exists(), "aphasia_corpus.json must exist"

    suite = AphasiaEvalSuite(corpus_path=corpus_path)
    result = suite.run()

    # Має впевнено детектити телеграфну мову
    assert result.true_positive_rate >= 0.8
    # Не має масово ламати нормальну мову
    assert result.true_negative_rate >= 0.8
    # Severity для телеграфних випадків має бути помітною
    assert result.mean_severity_telegraphic >= 0.3
