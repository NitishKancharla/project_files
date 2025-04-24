"""
Insurance Calculator:
A module for calculating insurance premiums based on FHIR medical data.

This module provides functionality to analyze FHIR (Fast Healthcare Interoperability Resources)
medical data and calculate insurance eligibility and premiums. It processes various medical
resources including patient information, conditions, observations, procedures, and medications
to make insurance-related decisions.

Dependencies:
    - fhirclient (for FHIR resource models)
    - datetime
    - typing
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional

from fhir.resources.patient import Patient
from fhir.resources.condition import Condition
from fhir.resources.observation import Observation
from fhir.resources.procedure import Procedure
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.encounter import Encounter
from fhir.resources.immunization import Immunization
from fhir.resources.diagnosticreport import DiagnosticReport


class InsuranceCalculator:
    """
    A calculator for determining insurance eligibility and premiums based on FHIR medical data.

    This class analyzes various FHIR resources to make insurance-related decisions, including
    eligibility determination and premium calculations. It takes into account multiple factors
    such as age, medical conditions, procedures, medications, and lifestyle factors.

    Attributes:
        patient (Patient): FHIR Patient resource.
        conditions (List[Condition]): List of patient's medical conditions.
        observations (List[Observation]): List of clinical observations.
        procedures (List[Procedure]): List of medical procedures.
        medications (List[MedicationRequest]): List of medication prescriptions.
        base_premium (float): Base monthly premium amount.
        risk_multiplier (float): Risk factor multiplier for premium calculation.
        disqualifying_conditions (List[str]): List of conditions that make patient ineligible.
        risk_factors (List[str]): List of identified risk factors.

    Note:
        All FHIR resources are expected to follow the FHIR R4 specification.
    """

    def __init__(self, fhir_bundle: Dict):
        """
        Initialize the calculator with FHIR data.

        Args:
            fhir_bundle (Dict): FHIR Bundle resource containing patient data in R4 format.
        """
        self.patient = None
        self.conditions: List[Condition] = []
        self.observations: List[Observation] = []
        self.procedures: List[Procedure] = []
        self.medications: List[MedicationRequest] = []
        self.encounters: List[Encounter] = []
        self.immunizations: List[Immunization] = []
        self.diagnostic_reports: List[DiagnosticReport] = []
        self._parse_bundle(fhir_bundle)

        # Insurance parameters
        self.base_premium = 500  # Base monthly premium in USD
        self.risk_multiplier = 1.0  # Initial risk multiplier
        self.disqualifying_conditions: List[str] = []
        self.risk_factors: List[str] = []

    def _parse_bundle(self, bundle: Dict) -> None:
        """
        Parse FHIR Bundle and extract relevant resources into instance variables.

        Args:
            bundle (Dict): FHIR Bundle resource containing patient data entries.
        """
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType", None)

            # Map resources to appropriate FHIR classes
            if resource_type == "Patient":
                self.patient = Patient(**resource)
            elif resource_type == "Condition":
                self.conditions.append(
                    Condition(**resource))  # Medical diagnoses
            elif resource_type == "Observation":
                self.observations.append(
                    Observation(**resource)
                )  # Clinical measurements
            elif resource_type == "Procedure":
                # Medical procedures
                self.procedures.append(Procedure(**resource))
            elif resource_type == "MedicationRequest":
                self.medications.append(
                    MedicationRequest(**resource))  # Prescriptions
            elif resource_type == "Encounter":
                self.encounters.append(
                    Encounter(**resource))  # Healthcare visits
            elif resource_type == "Immunization":
                self.immunizations.append(
                    Immunization(**resource))  # Vaccinations
            elif resource_type == "DiagnosticReport":
                self.diagnostic_reports.append(
                    DiagnosticReport(**resource)
                )  # Lab reports

    def check_eligibility(self) -> Tuple[bool, List[str]]:
        """
        Determine insurance eligibility based on medical criteria.

        Evaluates the patient's data against various eligibility criteria including
        age, terminal illnesses, recent surgeries, chronic conditions, pregnancy
        risks, mental health conditions, substance abuse, and other factors.

        Returns:
            Tuple[bool, List[str]]: A tuple containing:
                - bool: True if eligible, False otherwise.
                - List[str]: List of disqualifying reasons if not eligible.
        """
        self.disqualifying_conditions = []

        # 1. Age-based eligibility (over 85 disqualifies)
        if self._calculate_patient_age() > 85:
            self.disqualifying_conditions.append("Applicant over 85 years old")

        # 2. Active terminal conditions (e.g., specific cancers)
        terminal_codes = [
            "C34.90",  # Lung cancer
            "C61.9",  # Prostate cancer
            "C50.919",  # Breast cancer
            "C18.9",  # Colon cancer
            "C91.00",  # Acute lymphoblastic leukemia
        ]
        for condition in self.conditions:
            code = condition.code.coding[0].code
            status = condition.clinicalStatus.coding[0].code
            if code in terminal_codes and status == "active":
                self.disqualifying_conditions.append(
                    f"Active terminal condition: {code}"
                )

        # 3. Recent major surgeries (within 6 months)
        recent_surgeries = [
            "27447",  # Coronary artery bypass graft (CABG)
            "33533",  # Heart transplant
            "50360",  # Kidney transplant
        ]
        for procedure in self.procedures:
            if self._days_ago(procedure.performedDateTime) < 180:
                if procedure.code.coding[0].code in recent_surgeries:
                    self.disqualifying_conditions.append(
                        "Recent major surgery")

        # 4. Unmanaged chronic conditions (diabetes, hypertension)
        chronic_conditions = ["E11.9", "I10"]  # Diabetes, hypertension
        uncontrolled = []
        for condition in self.conditions:
            if condition.code.coding[0].code in chronic_conditions:
                management = self._get_management_checks(condition)
                if (
                    sum(management.values()) < 2
                ):  # Less than 2/3 management criteria met
                    uncontrolled.append(condition.code.coding[0].code)
        if uncontrolled:
            self.disqualifying_conditions.append(
                f"Unmanaged chronic conditions: {', '.join(uncontrolled)}"
            )

        # 5. High-risk pregnancy
        if self._is_pregnant() and self._is_high_risk_pregnancy():
            self.disqualifying_conditions.append("High-risk pregnancy")

        # 6. Recent heart attack (within 6 months)
        for condition in self.conditions:
            code = condition.code.coding[0].code
            status = condition.clinicalStatus.coding[0].code
            if code.startswith("I21") and status == "active":
                if self._days_ago(condition.onsetDateTime) < 180:
                    self.disqualifying_conditions.append("Recent heart attack")

        # 7. End-stage renal disease
        for condition in self.conditions:
            if (
                condition.code.coding[0].code == "N18.6"
                and condition.clinicalStatus.coding[0].code == "active"
            ):
                self.disqualifying_conditions.append("End-stage renal disease")

        # 8. Active cancer treatment
        if self._has_active_cancer_treatment():
            self.disqualifying_conditions.append("Active cancer treatment")

        # 9. Severe mental health conditions
        # Schizophrenia, bipolar, severe depression
        mental_health_codes = ["F20", "F31", "F32.5", "F33.3"]
        for condition in self.conditions:
            if (
                condition.code.coding[0].code in mental_health_codes
                and condition.clinicalStatus.coding[0].code == "active"
            ):
                self.disqualifying_conditions.append(
                    f"Severe mental health condition: {condition.code.coding[0].code}"
                )

        # 10. Active substance abuse
        substance_abuse_codes = [
            f"F{num}" for num in range(10, 20)]  # F10-F19 codes
        for condition in self.conditions:
            code_prefix = condition.code.coding[0].code[:3]
            if (
                code_prefix in substance_abuse_codes
                and condition.clinicalStatus.coding[0].code == "active"
            ):
                self.disqualifying_conditions.append(
                    f"Active substance abuse: {condition.code.coding[0].code}"
                )

        # 11. Recent organ transplant (within 6 months)
        transplant_codes = ["33533", "50360"]  # Heart and kidney transplants
        for procedure in self.procedures:
            if (
                procedure.code.coding[0].code in transplant_codes
                and self._days_ago(procedure.performedDateTime) < 180
            ):
                self.disqualifying_conditions.append("Recent organ transplant")

        # 12. Experimental treatment participation
        if self._in_experimental_treatment():
            self.disqualifying_conditions.append(
                "Experimental treatment participation")

        return (len(self.disqualifying_conditions) == 0, self.disqualifying_conditions)

    def calculate_premium(self) -> Optional[float]:
        """
        Calculate the adjusted monthly insurance premium based on risk factors.

        Adjusts the base premium using a risk multiplier determined by factors such
        as age, BMI, chronic conditions, lifestyle choices, medication adherence,
        and preventive care.

        Returns:
            float: The calculated monthly premium. Returns None if the patient is
                   not eligible for insurance.
        """
        if not self.check_eligibility()[0]:
            return None

        age = self._calculate_patient_age()
        # Age-based adjustments
        if age > 65:
            self.risk_multiplier *= 1.6  # Significant risk increase for seniors
        elif age > 50:
            self.risk_multiplier *= 1.3  # Moderate risk increase for age 50-65

        # BMI-based adjustments
        bmi = self._calculate_bmi()
        if bmi and bmi > 35:
            self.risk_multiplier *= 1.25  # High obesity risk
        elif bmi and bmi > 30:
            self.risk_multiplier *= 1.15  # Obesity risk

        # Chronic condition count adjustment
        chronic_count = sum(
            1
            for c in self.conditions
            if c.clinicalStatus.coding[0].code == "active"
            and any(cat.coding[0].code == "chronic" for cat in c.category)
        )
        if chronic_count > 2:
            self.risk_multiplier *= 1.35  # Multiple chronic conditions

        # Lifestyle factors
        if self._is_smoker():
            self.risk_multiplier *= 1.6  # Tobacco use
        if self._is_drinker():
            self.risk_multiplier *= 1.5  # Alcohol use

        # Health metrics
        if self._has_high_ldl():
            self.risk_multiplier *= 1.15  # Elevated cholesterol
        if self._has_family_history_heart_disease():
            self.risk_multiplier *= 1.2  # Family history of heart disease

        # Healthcare utilization patterns
        if self._has_frequent_er_visits():
            self.risk_multiplier *= 1.25  # Frequent ER visits

        # Environmental risk factors
        if self._has_high_risk_occupation():
            self.risk_multiplier *= 1.15  # Dangerous occupation
        if self._lives_in_high_pollution_area():
            self.risk_multiplier *= 1.1  # High pollution area

        # Medication adherence check
        for condition in self.conditions:
            if any("chronic" in [cat.coding[0].code for cat in condition.category]):
                management = self._get_management_checks(condition)
                if not management.get("medication_adherence"):
                    self.risk_multiplier *= 1.2  # Poor medication adherence
                    break

        # High-risk medication use
        if self._uses_high_risk_meds():
            self.risk_multiplier *= 1.2  # Medications with significant side effects

        # Preventive care status
        preventive = self._has_preventive_care()
        if not preventive.get("vaccinations"):
            self.risk_multiplier *= 1.1  # Missing required vaccinations

        # Positive preventive care adjustment
        if preventive.get("overall"):
            self.risk_multiplier *= 0.95  # Discount for comprehensive preventive care

        return round(self.base_premium * self.risk_multiplier, 2)

    # Helper methods ----------------------------------------------------------
    def _calculate_patient_age(self) -> int:
        """Calculate the patient's current age based on birthDate."""
        birth_date = datetime.strptime(self.patient.birthDate, "%Y-%m-%d")
        today = datetime.today()
        return (
            today.year
            - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
        )

    def _get_observation_value(self, code: str) -> Optional[float]:
        """Get latest numerical observation value by LOINC code."""
        for obs in reversed(self.observations):
            if obs.code.coding[0].code == code:
                return float(obs.valueQuantity.value)
        return None

    def _calculate_bmi(self) -> Optional[float]:
        """Calculate BMI from height and weight observations."""
        height = self._get_observation_value("8302-2")  # LOINC code for height
        weight = self._get_observation_value(
            "29463-7")  # LOINC code for weight
        return weight / ((height / 100) ** 2) if height and weight else None

    def _is_smoker(self) -> bool:
        """Check smoking status via tobacco use observation."""
        smoking_code = "72166-2"  # LOINC code for tobacco smoking status
        for obs in self.observations:
            if obs.code.coding[0].code == smoking_code and obs.valueCodeableConcept:
                return "smok" in obs.valueCodeableConcept.text.lower()
        return False

    def _is_drinker(self) -> bool:
        """Check alcohol consumption status."""
        alcohol_code = "74013-4"  # LOINC code for alcohol use
        for obs in self.observations:
            if obs.code.coding[0].code == alcohol_code and obs.valueCodeableConcept:
                return obs.valueCodeableConcept.text.lower() in ["yes", "current"]
        return any(
            c.code.coding[0].code in ["F10.10", "F10.20"] for c in self.conditions
        )

    def _has_high_ldl(self) -> bool:
        """Check for elevated LDL cholesterol (>190 mg/dL)."""
        ldl = self._get_observation_value("18262-6")  # LDL cholesterol code
        return ldl >= 190 if ldl else False

    def _has_family_history_heart_disease(self) -> bool:
        """Check for family history of heart disease."""
        return any(
            c.code.coding[0].code in ["Z82.49", "Z82.41"] for c in self.conditions
        )

    def _has_frequent_er_visits(self) -> bool:
        """Check for 3+ ER visits in the last year."""
        er_visits = [
            e for e in self.encounters if e.type[0].coding[0].code == "ER"]
        return sum(1 for e in er_visits if self._days_ago(e.period.start) < 365) >= 3

    def _has_high_risk_occupation(self) -> bool:
        """Check for high-risk occupations."""
        occupation_code = "67875-1"  # LOINC occupation code
        risky_jobs = {"construction", "firefighter", "police", "miner"}
        for obs in self.observations:
            if (
                obs.code.coding[0].code == occupation_code
                and obs.valueString.lower() in risky_jobs
            ):
                return True
        return False

    def _lives_in_high_pollution_area(self) -> bool:
        """Check residence in high pollution ZIP codes."""
        high_pollution_zips = {"10001", "90001", "60601"}
        return any(
            addr.postalCode in high_pollution_zips for addr in self.patient.address
        )

    def _get_management_checks(self, condition: Condition) -> Dict[str, bool]:
        """Evaluate management status for a chronic condition."""
        checks = {
            "provider_visit": False,
            "medication_adherence": False,
            "lab_monitoring": False,
        }
        condition_code = condition.code.coding[0].code

        # 1. Provider visit check (same condition documented in encounters)
        for enc in self.encounters:
            if self._days_ago(enc.period.start) < 365:
                # Check if encounter was for this specific condition
                if any(
                    coding.code == condition_code for coding in enc.reasonCode[0].coding
                ):
                    checks["provider_visit"] = True
                    break

        # 2. Medication adherence check
        condition_meds = [
            med
            for med in self.medications
            if any(coding.code == condition_code for coding in med.reasonCode[0].coding)
        ]
        if condition_meds:
            # Active prescriptions within last year
            active_meds = [
                med
                for med in condition_meds
                if med.status == "active"
                and self._days_ago(med.authoredOn) < 365
            ]
            checks["medication_adherence"] = len(active_meds) > 0

        # 3. Lab monitoring check
        lab_requirements = {
            "E11.9": {  # Type 2 diabetes
                "codes": ["4548-4", "2345-7"],  # HbA1c  # Blood glucose
                "frequency": 180,
            },
            "I10": {  # Essential hypertension
                "codes": ["55284-4"],  # Blood pressure panel
                "frequency": 90,
            },
        }
        if condition_code in lab_requirements:
            reqs = lab_requirements[condition_code]
            checks["lab_monitoring"] = any(
                obs.code.coding[0].code in reqs["codes"]
                and self._days_ago(obs.effectiveDateTime) < reqs["frequency"]
                for obs in self.observations
            )

        return checks

    def _uses_high_risk_meds(self) -> bool:
        """Check for medications with significant risk profiles."""
        high_risk_meds = {
            "warfarin",  # Anticoagulant - bleeding risk
            "insulin",  # Hypoglycemia risk
            "chemotherapy",
            "antipsychotic",
            "immunosuppressant",
        }
        for med in self.medications:
            if med.medicationCodeableConcept.text:
                name = med.medicationCodeableConcept.text.lower()
                if any(hr_term in name for hr_term in high_risk_meds):
                    return True
        return False

    def _has_preventive_care(self) -> dict:
        """Evaluate completion of recommended preventive care measures."""
        checks = {"vaccinations": False,
                  "screenings": False, "wellness_visit": False}

        # Vaccination check
        required_vaccines = self._get_required_vaccines()
        received_vaccines = {
            imm.vaccineCode.coding[0].code
            for imm in self.immunizations
            if self._days_ago(imm.occurrenceDateTime) < 366
        }
        checks["vaccinations"] = all(
            vax in received_vaccines for vax in required_vaccines
        )

        # Screening check
        checks["screenings"] = self._has_required_screenings(
            self._calculate_patient_age(), self.patient.gender
        )

        # Wellness visit check (CPT 185347001 - Annual wellness visit)
        checks["wellness_visit"] = any(
            enc.type[0].coding[0].code == "185347001"
            and self._days_ago(enc.period.start) < 730
            for enc in self.encounters
        )

        checks["overall"] = all(checks.values())
        return checks

    def _is_pregnant(self) -> bool:
        """Check current pregnancy status through observations."""
        # LOINC 82810-3: Pregnancy status
        return any(
            obs.code.coding[0].code == "82810-3"
            for obs in self.observations
        )

    def _is_high_risk_pregnancy(self) -> bool:
        """Identify high-risk pregnancy conditions."""
        high_risk_codes = {
            "O09.90",  # Supervision of high risk pregnancy, unspecified
            "O24.419",  # Pre-existing type 2 diabetes complicating pregnancy
            "O30.90",  # Multiple gestation pregnancy, unspecified
        }
        return any(
            condition.code.coding[0].code in high_risk_codes
            for condition in self.conditions
        )

    def _days_ago(self, date_str: str) -> int:
        """Calculate days elapsed since a given ISO date string."""
        if not date_str:
            return float("inf")  # Treat missing dates as ancient
        return (datetime.now() - datetime.strptime(date_str, "%Y-%m-%d")).days

    def _get_required_vaccines(self) -> List[str]:
        """Determine vaccines required based on patient demographics."""
        age = self._calculate_patient_age()
        vaccines = []

        # Universal recommendations
        vaccines.append("140")  # Influenza, seasonal (LOINC 140-4)

        # Age-based recommendations
        if age >= 50:
            vaccines.append("17")  # Zoster vaccine (LOINC 17-1)
        if age >= 65:
            vaccines.append("33")  # Pneumococcal (LOINC 33-1)

        # Gender-specific
        if self.patient.gender == "female" and age < 26:
            vaccines.append("62")  # HPV (LOINC 62-7)

        return vaccines

    def _has_required_screenings(self, age: int, gender: str) -> bool:
        """Verify completion of age/gender appropriate health screenings."""
        screenings = []

        # Blood pressure screening (LOINC 85354-9)
        if age >= 18:
            screenings.append(
                any(
                    self._days_ago(obs.effectiveDateTime) < 730
                    for obs in self.observations
                    if obs.code.coding[0].code == "85354-9"
                )
            )

        # Cancer screenings
        if gender == "female":
            if age >= 21:  # Pap smear (LOINC 47527-7)
                screenings.append(
                    any(
                        self._days_ago(dr.effectiveDateTime) < 1095
                        for dr in self.diagnostic_reports
                        if dr.code.coding[0].code == "47527-7"
                    )
                )
            if age >= 40:  # Mammogram (LOINC 24604-1)
                screenings.append(
                    any(
                        self._days_ago(dr.effectiveDateTime) < 730
                        for dr in self.diagnostic_reports
                        if dr.code.coding[0].code == "24604-1"
                    )
                )

        # Colon cancer screening
        if age >= 45:
            screenings.append(
                any(
                    # Colonoscopy/Stool DNA
                    dr.code.coding[0].code in {"47519-4", "74211-9"}
                    and self._days_ago(dr.effectiveDateTime) < 1825
                    for dr in self.diagnostic_reports
                )
            )

        return all(screenings)

    def _has_active_cancer_treatment(self) -> bool:
        """Identify active cancer therapies."""
        treatment_codes = {
            "Z51.11",  # Chemotherapy session
            "36656000",  # Chemotherapy (SNOMED)
            "1217123003",  # Radiation therapy
        }
        return any(
            proc.code.coding[0].code in treatment_codes
            and self._days_ago(proc.performedDateTime) < 180
            for proc in self.procedures
        )

    def _in_experimental_treatment(self) -> bool:
        """Detect participation in experimental therapies."""
        # Z00.6: Encounter for examination for normal comparison
        # in clinical research program
        return any(
            proc.code.coding[0].code == "Z00.6" for proc in self.procedures
        ) or any(
            "experimental" in med.medicationCodeableConcept.text.lower()
            for med in self.medications
        )
