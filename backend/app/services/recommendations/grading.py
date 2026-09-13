"""Score grading helpers that workers may import without touching the policy module.

`policy` gathers the workers, so a worker cannot import it at module load. This tiny
module has no such dependency.
"""


def graded(base: int, magnitude: float, span: int, cap: int) -> int:
    """Scale a rule's floor score by how far past its threshold the finding sits.

    `magnitude` is a 0..1 fraction of the way from the trigger point to the point
    the policy treats as fully severe. Bands are policy, not calibrated risk.
    """
    return int(min(cap, base + round(span * max(0.0, min(1.0, magnitude)))))
