
import time
import threading

from interaction.base_interaction import OffInteraction, DebugInteraction, IsHoldingInteraction
from interaction.phi_band_interaction import PhiBandInteraction
from interaction.theta_interaction import ThetaInteraction
from interaction.directional_tension_interaction import DirectionalTensionInteraction
from interaction.efficiency_interaction import EfficiencyInteraction
from interaction.resultant_phi_interaction import ResultantDirection
from interaction.max_force_interaction import MaxForceInteraction

class InteractionEngine:
    def __init__(self, config, device_manager, data_buffer, mqtt_manager, state_manager, fps = 15):
        self.config = config
        self.device_mgr = device_manager
        self.buffer = data_buffer
        self.mqtt = mqtt_manager
        self.state = state_manager
        self.FPS = fps

        self.interactions = {
            "Off": OffInteraction("Off", self.device_mgr, self.buffer, self.mqtt, self.state),
            "DebugOn": DebugInteraction("DebugOn", self.device_mgr, self.buffer, self.mqtt, self.state),
            "DebugHolding": IsHoldingInteraction("DebugHolding", self.device_mgr, self.buffer, self.mqtt, self.state),
            "PhiBand": PhiBandInteraction("PhiBand", self.device_mgr, self.buffer, self.mqtt, self.state),
            "ResultantDirection": ResultantDirection("PhiBand", self.device_mgr, self.buffer, self.mqtt, self.state),
            "Theta": ThetaInteraction("Theta", self.device_mgr, self.buffer, self.mqtt, self.state),
            "DirectionalTension": DirectionalTensionInteraction("DirectionalTension", self.device_mgr, self.buffer, self.mqtt, self.state),
            "Efficiency": EfficiencyInteraction("Efficiency", self.device_mgr, self.buffer, self.mqtt, self.state),
            "MaxForce": MaxForceInteraction("MaxForce", self.device_mgr, self.buffer, self.mqtt, self.state),
        }

        default_interaction = "Off"
        if not self.state.get("interaction/active"):
            self.state.set("interaction/active", default_interaction)

        self.set_interaction(self.state.get("interaction/active", default_interaction))


    def start_engine(self):
        self.running = True
        self.thread = threading.Thread(target=self._loop)
        self.thread.daemon = True
        self.thread.start()

    def stop_engine(self):
        self.running = False
        self.thread.join()

    def get_interaction(self):
        interaction_name = self.state.get("interaction/active", "Off")
        return self.interactions[interaction_name]

    def set_interaction(self, interaction_name):
        if interaction_name not in self.interactions:
            return

        interaction = self.get_interaction()
        param_path = f"interaction/params/{interaction_name}"
        config = self.state.get(param_path, {})

        clean_config = {
            k: v["value"]
            for k, v in config.items()
            if isinstance(v, dict) and "value" in v
        }
        interaction.update_config(clean_config)
        interaction.on_select()

    def stop(self):
        self.running = False
        self.thread.join()

    def _loopstep(self):
        self.update()
        time.sleep(1.0 / self.FPS)

    def _loop(self):
        while self.running:
            if self.config['DEBUG']:
                self._loopstep()
            else:
                try:
                    self._loopstep()
                except Exception as e:
                    print(f"[InteractionEngine] Error in loop: {e}")


    def update(self):
        interaction = self.get_interaction()
        if interaction:
            interaction.update()
