from typing import List

class ReferenceMapper:
    @staticmethod
    def get_references(cve: str) -> List[str]:
        return [
            f"https://nvd.nist.gov/vuln/detail/{cve}",
            f"https://cve.mitre.org/cgi-bin/cvename.cgi?name={cve}"
        ]
