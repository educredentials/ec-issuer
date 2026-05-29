from dataclasses import dataclass


@dataclass
class Criteria:
    narrative: str


@dataclass
class Achievement:
    id: str
    type: list[str]
    criteria: Criteria
    description: str
    name: str


@dataclass
class CredentialSubject:
    id: str
    type: list[str]
    achievement: Achievement


@dataclass
class Award:
    credentialSubject: CredentialSubject

    @staticmethod
    def default() -> "Award":
        return Award(
            credentialSubject=CredentialSubject(
                id="did:example:ebfeb1f712ebc6f1c276e12ec21",
                type=["AchievementSubject"],
                achievement=Achievement(
                    id="https://example.com/achievements/example",
                    type=["Achievement"],
                    criteria=Criteria(
                        narrative=(
                            "Team members are nominated for this badge by their peers."
                        )
                    ),
                    description="This badge recognizes ability to work in a team.",
                    name="Teamwork",
                ),
            )
        )
