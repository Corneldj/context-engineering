import unittest

from ce import MockModel, ToolRegistry, call, say
from exercises._loader import load

ex = load("ex04_external_verifier")


def build_world():
    world = {"deployed": False}
    reg = ToolRegistry()

    @reg.register("deploy", "Deploys the service.", {})
    def deploy() -> str:
        world["deployed"] = True
        return "deployed ok"

    return world, reg


class TestExternalVerification(unittest.TestCase):
    def test_the_liar_is_not_believed(self):
        world, reg = build_world()
        liar = MockModel(policy=lambda t, m: say("Deployed successfully! All good."))
        outcome = ex.make_loop(liar, reg, world).run("deploy the service")
        self.assertFalse(outcome.ok, "the loop accepted a claim the world contradicts")
        self.assertFalse(world["deployed"])

    def test_the_liar_is_stopped_quickly(self):
        world, reg = build_world()
        liar = MockModel(policy=lambda t, m: say("Deployed successfully!"))
        outcome = ex.make_loop(liar, reg, world).run("deploy the service")
        self.assertLessEqual(outcome.iterations, 5,
                             "a model that changes nothing should stop fast")

    def test_the_worker_succeeds(self):
        world, reg = build_world()
        worker = MockModel(script=[call("deploy"), say("done")])
        outcome = ex.make_loop(worker, reg, world).run("deploy the service")
        self.assertTrue(outcome.ok)
        self.assertTrue(world["deployed"])

    def test_the_verifier_tier_is_deterministic(self):
        from ce import Tier
        world, reg = build_world()
        loop = ex.make_loop(MockModel(), reg, world)
        self.assertEqual(loop.verifier.tier, Tier.DETERMINISTIC)


if __name__ == "__main__":
    unittest.main()
