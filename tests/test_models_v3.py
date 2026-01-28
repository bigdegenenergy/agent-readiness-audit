"""Tests for v3 scoring models and functions."""

from __future__ import annotations

from agent_readiness_audit.models import (
    DOMAIN_WEIGHTS,
    AgentGrade,
    DomainScore,
    calculate_domain_score,
    calculate_overall_score,
    get_grade_description,
    get_grade_for_score,
)


class TestDomainWeights:
    """Tests for DOMAIN_WEIGHTS validation."""

    def test_domain_weights_sum_to_one(self) -> None:
        """Verify that domain weights sum to 1.0 (100%)."""
        total = sum(DOMAIN_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001, f"Weights sum to {total}, expected 1.0"

    def test_all_domains_have_weights(self) -> None:
        """Verify all expected domains have weights defined."""
        expected_domains = {
            "structure",
            "interfaces",
            "determinism",
            "security",
            "testing",
            "ergonomics",
        }
        assert set(DOMAIN_WEIGHTS.keys()) == expected_domains

    def test_all_weights_are_positive(self) -> None:
        """Verify all weights are positive values."""
        for domain, weight in DOMAIN_WEIGHTS.items():
            assert weight > 0, f"Domain {domain} has non-positive weight {weight}"

    def test_specific_weight_values(self) -> None:
        """Verify specific weight values match spec."""
        assert DOMAIN_WEIGHTS["structure"] == 0.15  # 15%
        assert DOMAIN_WEIGHTS["interfaces"] == 0.20  # 20%
        assert DOMAIN_WEIGHTS["determinism"] == 0.20  # 20%
        assert DOMAIN_WEIGHTS["security"] == 0.20  # 20%
        assert DOMAIN_WEIGHTS["testing"] == 0.15  # 15%
        assert DOMAIN_WEIGHTS["ergonomics"] == 0.10  # 10%


class TestCalculateDomainScore:
    """Tests for calculate_domain_score function."""

    def test_perfect_score(self) -> None:
        """All checks passed should give 100."""
        score = calculate_domain_score(passed=10, total=10)
        assert score == 100.0

    def test_zero_score(self) -> None:
        """No checks passed should give 0."""
        score = calculate_domain_score(passed=0, total=10)
        assert score == 0.0

    def test_partial_score(self) -> None:
        """Partial passes should give proportional score."""
        score = calculate_domain_score(passed=5, total=10)
        assert score == 50.0

    def test_empty_domain(self) -> None:
        """Domain with no checks should return 0."""
        score = calculate_domain_score(passed=0, total=0)
        assert score == 0.0

    def test_single_check_passed(self) -> None:
        """Single check passed should give 100."""
        score = calculate_domain_score(passed=1, total=1)
        assert score == 100.0

    def test_single_check_failed(self) -> None:
        """Single check failed should give 0."""
        score = calculate_domain_score(passed=0, total=1)
        assert score == 0.0


class TestCalculateOverallScore:
    """Tests for calculate_overall_score function."""

    def test_perfect_scores_all_domains(self) -> None:
        """Perfect scores in all domains should give 100."""
        domain_scores = {
            "structure": DomainScore(
                name="structure", score=100.0, weight=DOMAIN_WEIGHTS["structure"]
            ),
            "interfaces": DomainScore(
                name="interfaces", score=100.0, weight=DOMAIN_WEIGHTS["interfaces"]
            ),
            "determinism": DomainScore(
                name="determinism", score=100.0, weight=DOMAIN_WEIGHTS["determinism"]
            ),
            "security": DomainScore(
                name="security", score=100.0, weight=DOMAIN_WEIGHTS["security"]
            ),
            "testing": DomainScore(
                name="testing", score=100.0, weight=DOMAIN_WEIGHTS["testing"]
            ),
            "ergonomics": DomainScore(
                name="ergonomics", score=100.0, weight=DOMAIN_WEIGHTS["ergonomics"]
            ),
        }
        overall = calculate_overall_score(domain_scores)
        assert overall == 100.0

    def test_zero_scores_all_domains(self) -> None:
        """Zero scores in all domains should give 0."""
        domain_scores = {
            "structure": DomainScore(
                name="structure", score=0.0, weight=DOMAIN_WEIGHTS["structure"]
            ),
            "interfaces": DomainScore(
                name="interfaces", score=0.0, weight=DOMAIN_WEIGHTS["interfaces"]
            ),
            "determinism": DomainScore(
                name="determinism", score=0.0, weight=DOMAIN_WEIGHTS["determinism"]
            ),
            "security": DomainScore(
                name="security", score=0.0, weight=DOMAIN_WEIGHTS["security"]
            ),
            "testing": DomainScore(
                name="testing", score=0.0, weight=DOMAIN_WEIGHTS["testing"]
            ),
            "ergonomics": DomainScore(
                name="ergonomics", score=0.0, weight=DOMAIN_WEIGHTS["ergonomics"]
            ),
        }
        overall = calculate_overall_score(domain_scores)
        assert overall == 0.0

    def test_weighted_calculation(self) -> None:
        """Verify weighted calculation is correct."""
        # Security only at 100 (weight 0.20), others at 0
        domain_scores = {
            "structure": DomainScore(
                name="structure", score=0.0, weight=DOMAIN_WEIGHTS["structure"]
            ),
            "interfaces": DomainScore(
                name="interfaces", score=0.0, weight=DOMAIN_WEIGHTS["interfaces"]
            ),
            "determinism": DomainScore(
                name="determinism", score=0.0, weight=DOMAIN_WEIGHTS["determinism"]
            ),
            "security": DomainScore(
                name="security", score=100.0, weight=DOMAIN_WEIGHTS["security"]
            ),
            "testing": DomainScore(
                name="testing", score=0.0, weight=DOMAIN_WEIGHTS["testing"]
            ),
            "ergonomics": DomainScore(
                name="ergonomics", score=0.0, weight=DOMAIN_WEIGHTS["ergonomics"]
            ),
        }
        overall = calculate_overall_score(domain_scores)
        # Should be 100 * 0.20 = 20
        assert overall == 20.0

    def test_mixed_scores(self) -> None:
        """Test with mixed domain scores."""
        domain_scores = {
            "structure": DomainScore(
                name="structure", score=80.0, weight=DOMAIN_WEIGHTS["structure"]
            ),
            "interfaces": DomainScore(
                name="interfaces", score=70.0, weight=DOMAIN_WEIGHTS["interfaces"]
            ),
            "determinism": DomainScore(
                name="determinism", score=60.0, weight=DOMAIN_WEIGHTS["determinism"]
            ),
            "security": DomainScore(
                name="security", score=90.0, weight=DOMAIN_WEIGHTS["security"]
            ),
            "testing": DomainScore(
                name="testing", score=50.0, weight=DOMAIN_WEIGHTS["testing"]
            ),
            "ergonomics": DomainScore(
                name="ergonomics", score=40.0, weight=DOMAIN_WEIGHTS["ergonomics"]
            ),
        }
        overall = calculate_overall_score(domain_scores)
        # 80*0.15 + 70*0.20 + 60*0.20 + 90*0.20 + 50*0.15 + 40*0.10
        # = 12 + 14 + 12 + 18 + 7.5 + 4 = 67.5
        assert overall == 67.5

    def test_updates_weighted_score_on_domain(self) -> None:
        """Verify weighted_score is updated on DomainScore objects."""
        domain_scores = {
            "security": DomainScore(
                name="security", score=80.0, weight=DOMAIN_WEIGHTS["security"]
            ),
        }
        calculate_overall_score(domain_scores)
        assert domain_scores["security"].weighted_score == 80.0 * 0.20

    def test_fallback_to_default_weight(self) -> None:
        """Test fallback to DOMAIN_WEIGHTS if weight is 0."""
        domain_scores = {
            "security": DomainScore(
                name="security",
                score=100.0,
                weight=0.0,  # Zero weight
            ),
        }
        overall = calculate_overall_score(domain_scores)
        # Should fall back to DOMAIN_WEIGHTS["security"] = 0.20
        assert overall == 20.0


class TestGetGradeForScore:
    """Tests for get_grade_for_score function."""

    def test_agent_first_threshold(self) -> None:
        """90+ should be Agent-First."""
        assert get_grade_for_score(90.0) == AgentGrade.AGENT_FIRST
        assert get_grade_for_score(95.0) == AgentGrade.AGENT_FIRST
        assert get_grade_for_score(100.0) == AgentGrade.AGENT_FIRST

    def test_agent_compatible_threshold(self) -> None:
        """75-89 should be Agent-Compatible."""
        assert get_grade_for_score(75.0) == AgentGrade.AGENT_COMPATIBLE
        assert get_grade_for_score(80.0) == AgentGrade.AGENT_COMPATIBLE
        assert get_grade_for_score(89.9) == AgentGrade.AGENT_COMPATIBLE

    def test_human_first_risky_threshold(self) -> None:
        """60-74 should be Human-First, Agent-Risky."""
        assert get_grade_for_score(60.0) == AgentGrade.HUMAN_FIRST_RISKY
        assert get_grade_for_score(70.0) == AgentGrade.HUMAN_FIRST_RISKY
        assert get_grade_for_score(74.9) == AgentGrade.HUMAN_FIRST_RISKY

    def test_agent_hostile_threshold(self) -> None:
        """Below 60 should be Agent-Hostile."""
        assert get_grade_for_score(0.0) == AgentGrade.AGENT_HOSTILE
        assert get_grade_for_score(30.0) == AgentGrade.AGENT_HOSTILE
        assert get_grade_for_score(59.9) == AgentGrade.AGENT_HOSTILE

    def test_boundary_values(self) -> None:
        """Test exact boundary values."""
        # 89.99... should be Agent-Compatible (just under 90)
        assert get_grade_for_score(89.999) == AgentGrade.AGENT_COMPATIBLE
        # 90 should be Agent-First
        assert get_grade_for_score(90.0) == AgentGrade.AGENT_FIRST


class TestGetGradeDescription:
    """Tests for get_grade_description function."""

    def test_agent_first_description(self) -> None:
        """Agent-First should have description."""
        desc = get_grade_description(AgentGrade.AGENT_FIRST)
        assert desc
        assert "autonomous" in desc.lower() or "optimized" in desc.lower()

    def test_agent_compatible_description(self) -> None:
        """Agent-Compatible should have description."""
        desc = get_grade_description(AgentGrade.AGENT_COMPATIBLE)
        assert desc
        assert "minor" in desc.lower() or "friction" in desc.lower()

    def test_human_first_risky_description(self) -> None:
        """Human-First, Agent-Risky should have description."""
        desc = get_grade_description(AgentGrade.HUMAN_FIRST_RISKY)
        assert desc
        assert "risk" in desc.lower() or "human" in desc.lower()

    def test_agent_hostile_description(self) -> None:
        """Agent-Hostile should have description."""
        desc = get_grade_description(AgentGrade.AGENT_HOSTILE)
        assert desc
        assert "unsuitable" in desc.lower() or "hostile" in desc.lower()


class TestDomainScoreModel:
    """Tests for DomainScore Pydantic model."""

    def test_default_values(self) -> None:
        """Test default values for DomainScore."""
        ds = DomainScore(name="test")
        assert ds.name == "test"
        assert ds.score == 0.0
        assert ds.weight == 0.0
        assert ds.weighted_score == 0.0
        assert ds.checks == []
        assert ds.passed_checks == 0
        assert ds.total_checks == 0

    def test_percentage_property(self) -> None:
        """Test percentage property returns score."""
        ds = DomainScore(name="test", score=75.0)
        assert ds.percentage == 75.0

    def test_with_all_fields(self) -> None:
        """Test DomainScore with all fields populated."""
        ds = DomainScore(
            name="security",
            description="Security domain",
            score=85.0,
            weight=0.20,
            weighted_score=17.0,
            passed_checks=8,
            total_checks=10,
            evidence=["Evidence 1", "Evidence 2"],
            red_flags=["Flag 1"],
        )
        assert ds.name == "security"
        assert ds.description == "Security domain"
        assert ds.score == 85.0
        assert ds.weight == 0.20
        assert ds.weighted_score == 17.0
        assert ds.passed_checks == 8
        assert ds.total_checks == 10
        assert len(ds.evidence) == 2
        assert len(ds.red_flags) == 1


class TestAgentGradeEnum:
    """Tests for AgentGrade enum."""

    def test_enum_values(self) -> None:
        """Test enum has correct string values."""
        assert AgentGrade.AGENT_FIRST.value == "Agent-First"
        assert AgentGrade.AGENT_COMPATIBLE.value == "Agent-Compatible"
        assert AgentGrade.HUMAN_FIRST_RISKY.value == "Human-First, Agent-Risky"
        assert AgentGrade.AGENT_HOSTILE.value == "Agent-Hostile"

    def test_enum_membership(self) -> None:
        """Test enum has exactly 4 members."""
        assert len(AgentGrade) == 4
