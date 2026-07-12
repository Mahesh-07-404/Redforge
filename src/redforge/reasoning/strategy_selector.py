class StrategySelector:
    @staticmethod
    def select_strategy(goal_text: str) -> str:
        gt = goal_text.lower()
        if "passive" in gt:
            return "Passive Recon"
        elif "active" in gt:
            return "Active Recon"
        elif "bug bounty" in gt:
            return "Bug Bounty"
        elif "ctf" in gt:
            return "CTF"
        elif "learning" in gt:
            return "Learning"
        elif "research" in gt:
            return "Research"
        elif "android" in gt:
            return "Android"
        elif "network" in gt:
            return "Network"
        elif "cloud" in gt:
            return "Cloud"
        elif "api" in gt:
            return "API"
        return "Passive Recon"
