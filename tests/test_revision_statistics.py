import importlib.util
from pathlib import Path
import numpy as np
import pytest
spec=importlib.util.spec_from_file_location('revision_stats',Path(__file__).resolve().parents[1]/'scripts/66_revision_statistics.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test_null_centred_boundary_and_directions():
 d=np.tile([-.03,.03],10)-.02
 assert .4<m.null_studentized_p(d,.02)<.7
 assert m.null_studentized_p(d+.15,.02)<.01
 assert m.null_studentized_p(d-.15,.02)>.99
def test_location_scale_equivariance():
 d=np.array([-.04,-.03,-.01,0.,.01,.03,.06,.07])
 p=m.null_studentized_p(d,.02)
 assert p==m.null_studentized_p(3*d,.06)
 assert p==m.null_studentized_p(d+.005,.015)
@pytest.mark.parametrize('d',[[0.,np.nan],[1.],[[1.,2.]]])
def test_bad_participant_vectors_refused(d):
 with pytest.raises(ValueError):m.null_studentized_p(d,.02)
def test_holm_never_reduces_p_and_respects_order():
 p=np.array([.05,.001,.02,.5]);a=m.holm(p)
 assert (a>=p).all()
 assert np.all(np.diff(a[np.argsort(p)])>=0)
