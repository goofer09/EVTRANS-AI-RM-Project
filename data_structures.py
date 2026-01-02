from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Component:
    """Represents a single automotive component"""
    name: str
    cost_share: float  # 0.0-1.0 (20% = 0.2)
    
    # These fields get added by subsequent LLM calls
    classification: Optional[str] = None  # SHARED, ICE_ONLY, EV_ONLY
    similarity_score: Optional[float] = None  # 0.0-1.0
    
    # Scoring fields (6 dimensions, 0-100 each)
    tech_score: Optional[int] = None
    manufacturing_score: Optional[int] = None
    supply_chain_score: Optional[int] = None
    demand_score: Optional[int] = None
    value_score: Optional[int] = None
    regulatory_score: Optional[int] = None
    
    @property
    def tfs_score(self):
        """Calculate TFS (Transition Feasibility Score) if all scores exist"""
        scores = [
            self.tech_score,
            self.manufacturing_score,
            self.supply_chain_score,
            self.demand_score,
            self.value_score,
            self.regulatory_score
        ]
        
        # Only calculate if all scores are filled
        if None not in scores:
            return int(sum(scores) / len(scores))
        return None
    
    @property
    def timeline(self):
        """Estimate timeline based on TFS score"""
        if self.tfs_score is None:
            return None
        
        if self.tfs_score >= 75:
            return "1-2 years"
        elif self.tfs_score >= 60:
            return "2-3 years"
        elif self.tfs_score >= 40:
            return "3-5 years"
        else:
            return "5+ years"
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "cost_share": self.cost_share,
            "classification": self.classification,
            "similarity_score": self.similarity_score,
            "scores": {
                "technical": self.tech_score,
                "manufacturing": self.manufacturing_score,
                "supply_chain": self.supply_chain_score,
                "demand": self.demand_score,
                "value": self.value_score,
                "regulatory": self.regulatory_score
            },
            "tfs_score": self.tfs_score,
            "timeline": self.timeline
        }


@dataclass
class HSCode:
    """Represents an HS Code with its components"""
    code: str
    description: str
    components: List[Component] = field(default_factory=list)
    
    def add_components(self, component_data: List[dict]):
        """
        Add components after enrichment (LLM Call #1)
        
        Input: [
            {"name": "Brake pads", "cost_share": 0.2},
            {"name": "Calipers", "cost_share": 0.2},
            ...
        ]
        """
        self.components = [
            Component(name=c['name'], cost_share=c['cost_share'])
            for c in component_data
        ]
    
    def update_classifications(self, classification_data: List[dict]):
        """
        Update components with classification (LLM Call #2)
        
        Input: [
            {"name": "Brake pads", "classification": "SHARED", "similarity": 0.92},
            ...
        ]
        """
        for component, data in zip(self.components, classification_data):
            component.classification = data.get('classification')
            component.similarity_score = data.get('similarity_score')
    
    def update_scores(self, score_data: List[dict]):
        """
        Update components with scores (LLM Call #3)
        
        Input: [
            {
                "name": "Brake pads",
                "tech": 85,
                "manufacturing": 90,
                "supply_chain": 88,
                "demand": 85,
                "value": 80,
                "regulatory": 92
            },
            ...
        ]
        """
        for component, data in zip(self.components, score_data):
            component.tech_score = data.get('tech')
            component.manufacturing_score = data.get('manufacturing')
            component.supply_chain_score = data.get('supply_chain')
            component.demand_score = data.get('demand')
            component.value_score = data.get('value')
            component.regulatory_score = data.get('regulatory')
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "hs_code": self.code,
            "description": self.description,
            "components": [c.to_dict() for c in self.components]
        }