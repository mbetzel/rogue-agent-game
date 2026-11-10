# scratch wrapper: run_reference_bot_validation.py with red_secret_owner_yield=2 injected (and diag replay)
import sys, os, runpy
sys.path.insert(0, os.getcwd())
import scripts.run_reference_bot_validation as m
from sim.config import GameConfig
_orig = m.make_config
def mk(cfg_name, players, pr_push=False, pr_params=None, pr_scope="all"):
    from sim.config import PrPushParams
    kw = dict(num_players=players, bot_pr_push=bool(pr_push), red_secret_owner_yield=2)
    if pr_params: kw["bot_pr_push_params"] = PrPushParams(**pr_params)
    if pr_scope != "all": kw["bot_pr_push_scope"] = pr_scope
    return getattr(GameConfig, cfg_name)(**kw)
m.make_config = mk
if __name__ == "__main__":
    if sys.argv[1] == "diag":
        sys.argv = ["ref_diag.py"] + sys.argv[2:]
        sys.path.insert(0, "sim_results/v380_rsp1/ref1")
        runpy.run_path("sim_results/v380_rsp1/ref1/ref_diag.py", run_name="__main__")
    else:
        sys.argv = ["x"] + sys.argv[1:]
        m.main()
