import random

from django.core.management.base import BaseCommand

from apps.questions.models import Question
from apps.subjects.models import Subject


QUESTION_DATA = {
    "true_false": [
        {"q": "The sun is a star.", "a": ["True"], "e": "The sun is classified as a G-type main-sequence star."},
        {"q": "Water boils at 90°C at sea level.", "a": ["False"], "e": "Water boils at 100°C at sea level."},
        {"q": "The human body has 206 bones.", "a": ["True"], "e": "An adult human body contains 206 bones."},
        {"q": "Light travels faster than sound.", "a": ["True"], "e": "Light travels at approximately 300,000 km/s while sound travels at about 343 m/s."},
        {"q": "The capital of France is London.", "a": ["False"], "e": "The capital of France is Paris."},
        {"q": "Photosynthesis occurs in the leaves of plants.", "a": ["True"], "e": "Chloroplasts in leaf cells carry out photosynthesis."},
        {"q": "The chemical symbol for gold is Go.", "a": ["False"], "e": "The chemical symbol for gold is Au."},
        {"q": "DNA stands for Deoxyribonucleic Acid.", "a": ["True"], "e": "DNA is short for Deoxyribonucleic Acid."},
        {"q": "The Earth is flat.", "a": ["False"], "e": "The Earth is an oblate spheroid."},
        {"q": "Gravity pulls objects toward the centre of the Earth.", "a": ["True"], "e": "Gravity is a force that attracts objects toward the centre of the Earth."},
        {"q": "Mitochondria are known as the powerhouse of the cell.", "a": ["True"], "e": "Mitochondria produce ATP, the energy currency of the cell."},
        {"q": "An isotope has the same number of protons but different electrons.", "a": ["False"], "e": "Isotopes have the same number of protons but different numbers of neutrons."},
        {"q": "The past tense of 'go' is 'went'.", "a": ["True"], "e": "'Went' is the irregular past tense of 'go'."},
        {"q": "A simile compares two things using 'like' or 'as'.", "a": ["True"], "e": "Similes use 'like' or 'as' to make comparisons."},
        {"q": "The largest planet in the solar system is Saturn.", "a": ["False"], "e": "Jupiter is the largest planet in the solar system."},
        {"q": "Newton's first law is also called the law of inertia.", "a": ["True"], "e": "Newton's first law describes how objects resist changes in motion."},
        {"q": "Evaporation is the change from liquid to gas at the surface.", "a": ["True"], "e": "Evaporation occurs at the surface of a liquid below boiling point."},
        {"q": "The chemical formula for table salt is NaCl.", "a": ["True"], "e": "Table salt is sodium chloride (NaCl)."},
        {"q": "An adverb describes a noun.", "a": ["False"], "e": "Adverbs describe verbs, adjectives, or other adverbs, not nouns."},
        {"q": "The heart has four chambers.", "a": ["True"], "e": "The human heart has two atria and two ventricles, totalling four chambers."},
    ],
    "fill_blank": [
        {"q": "The chemical symbol for water is ____.", "a": ["H2O"], "e": "Water is composed of two hydrogen atoms and one oxygen atom."},
        {"q": "The process by which plants make food is called ____.", "a": ["photosynthesis"], "e": "Plants use sunlight, water, and CO2 to produce glucose."},
        {"q": "The boiling point of water is ____ degrees Celsius.", "a": ["100"], "e": "At standard atmospheric pressure, water boils at 100°C."},
        {"q": "The formula for calculating speed is ____.", "a": ["distance divided by time", "distance/time", "speed = distance/time"], "e": "Speed = Distance ÷ Time."},
        {"q": "The largest organ in the human body is the ____.", "a": ["skin"], "e": "The skin covers the entire body and is the largest organ."},
        {"q": "The past participle of 'eat' is ____.", "a": ["eaten"], "e": "The forms are: eat, ate, eaten."},
        {"q": "The powerhouse of the cell is the ____.", "a": ["mitochondria"], "e": "Mitochondria generate most of the cell's ATP supply."},
        {"q": "The gas in the atmosphere that absorbs heat is ____.", "a": ["carbon dioxide", "CO2"], "e": "Carbon dioxide is a major greenhouse gas."},
        {"q": "The closest star to Earth is the ____.", "a": ["Sun", "sun"], "e": "The Sun is approximately 150 million km from Earth."},
        {"q": "The formula for the area of a circle is ____.", "a": ["pi r squared", "πr²", "pi*r^2", "A = πr²"], "e": "Area = π × radius²."},
        {"q": "The study of living things is called ____.", "a": ["biology"], "e": "Biology is the scientific study of life and organisms."},
        {"q": "The chemical symbol for iron is ____.", "a": ["Fe"], "e": "Fe comes from the Latin word 'ferrum'."},
        {"q": "The instrument used to measure temperature is a ____.", "a": ["thermometer"], "e": "A thermometer measures temperature in Celsius or Fahrenheit."},
        {"q": "The process of a solid turning directly into a gas is called ____.", "a": ["sublimation"], "e": "Sublimation bypasses the liquid state entirely."},
        {"q": "The SI unit of force is the ____.", "a": ["Newton", "newton"], "e": "Named after Sir Isaac Newton, 1 N = 1 kg·m/s²."},
        {"q": "The plural of 'child' is ____.", "a": ["children"], "e": "'Child' is an irregular noun; its plural is 'children'."},
        {"q": "The chemical symbol for sodium is ____.", "a": ["Na"], "e": "Na comes from the Latin word 'natrium'."},
        {"q": "The force that opposes motion between two surfaces is called ____.", "a": ["friction"], "e": "Friction converts kinetic energy into heat energy."},
        {"q": "The part of the plant that absorbs water from the soil is the ____.", "a": ["root", "roots"], "e": "Roots anchor the plant and absorb water and minerals."},
        {"q": "The value of pi (π) to two decimal places is ____.", "a": ["3.14"], "e": "π ≈ 3.14159..."},
    ],
    "essay": [
        {"q": "Explain the process of photosynthesis and its importance to life on Earth.", "a": [], "e": "Discuss light absorption, chlorophyll, CO2 + H2O → glucose + O2, and why it sustains food chains."},
        {"q": "Describe the water cycle and explain how it affects weather patterns.", "a": [], "e": "Cover evaporation, condensation, precipitation, and collection stages."},
        {"q": "Discuss the causes and effects of climate change on the environment.", "a": [], "e": "Address greenhouse gases, deforestation, rising temperatures, sea level rise, and biodiversity loss."},
        {"q": "Explain Newton's three laws of motion with real-life examples.", "a": [], "e": "Law of inertia, F=ma, action-reaction pairs with everyday examples."},
        {"q": "Write an essay on the importance of clean water access for communities.", "a": [], "e": "Discuss health impacts, economic effects, and solutions for clean water access."},
        {"q": "Describe the structure of an animal cell and the function of each organelle.", "a": [], "e": "Cover nucleus, mitochondria, ribosomes, ER, Golgi apparatus, cell membrane."},
        {"q": "Discuss the role of the internet in modern education.", "a": [], "e": "Cover e-learning, accessibility, digital divide, and online resources."},
        {"q": "Explain the differences between renewable and non-renewable energy sources.", "a": [], "e": "Compare solar, wind, hydro vs fossil fuels; discuss sustainability and environmental impact."},
        {"q": "Write about the importance of wildlife conservation.", "a": [], "e": "Discuss biodiversity, ecosystem services, threats, and conservation strategies."},
        {"q": "Discuss how pollution affects human health and the environment.", "a": [], "e": "Cover air, water, and soil pollution; health effects; prevention measures."},
        {"q": "Explain the process of digestion in the human body from ingestion to absorption.", "a": [], "e": "Cover mouth, oesophagus, stomach, small intestine, large intestine, and nutrient absorption."},
        {"q": "Discuss the importance of education in national development.", "a": [], "e": "Address literacy, economic growth, social equality, and innovation."},
        {"q": "Describe the rock cycle and identify the three main types of rocks.", "a": [], "e": "Cover igneous, sedimentary, metamorphic, and how they transform."},
        {"q": "Explain the concept of natural selection and how it drives evolution.", "a": [], "e": "Discuss variation, survival of the fittest, reproduction, and adaptation over generations."},
        {"q": "Write about the effects of deforestation on the environment.", "a": [], "e": "Cover soil erosion, loss of biodiversity, climate impact, and water cycle disruption."},
        {"q": "Discuss the importance of food security in developing countries.", "a": [], "e": "Address causes of hunger, agricultural challenges, and policy solutions."},
        {"q": "Explain the structure and function of the human circulatory system.", "a": [], "e": "Cover heart, blood vessels, blood components, and oxygen transport."},
        {"q": "Discuss the advantages and disadvantages of urbanisation.", "a": [], "e": "Cover economic opportunities vs overcrowding, pollution, and strain on resources."},
        {"q": "Write an essay on the role of the judiciary in a democratic society.", "a": [], "e": "Discuss independence, rule of law, protection of rights, and checks on power."},
        {"q": "Explain the greenhouse effect and its impact on global warming.", "a": [], "e": "Cover solar radiation, heat trapping by gases, and consequences for the climate."},
    ],
    "matching": [
        {"q": "Match each element with its chemical symbol: Gold, Iron, Sodium, Potassium, Calcium", "a": ["Gold — Au", "Iron — Fe", "Sodium — Na", "Potassium — K", "Calcium — Ca"], "e": "These symbols come from Latin names: aurum, ferrum, natrium, kalium, calcium."},
        {"q": "Match each planet with its position from the Sun: Jupiter, Earth, Mars, Venus, Mercury", "a": ["Mercury — 1st", "Venus — 2nd", "Earth — 3rd", "Mars — 4th", "Jupiter — 5th"], "e": "The order of planets from the Sun is Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune."},
        {"q": "Match each organ with its function: Heart, Lungs, Liver, Kidneys, Brain", "a": ["Heart — Pumps blood", "Lungs — Gas exchange", "Liver — Detoxification", "Kidneys — Filter blood", "Brain — Controls body"], "e": "Each organ has a primary function in maintaining homeostasis."},
        {"q": "Match each part of speech with its example: Noun, Verb, Adjective, Adverb, Pronoun", "a": ["Noun — table", "Verb — run", "Adjective — beautiful", "Adverb — quickly", "Pronoun — he"], "e": "Parts of speech classify words by their function in a sentence."},
        {"q": "Match each scientist with their discovery: Newton, Einstein, Darwin, Pasteur, Tesla", "a": ["Newton — Laws of motion", "Einstein — Relativity", "Darwin — Natural selection", "Pasteur — Germ theory", "Tesla — Alternating current"], "e": "Each scientist made groundbreaking contributions to their field."},
        {"q": "Match each vitamin with its deficiency disease: A, C, D, B12, K", "a": ["Vitamin A — Night blindness", "Vitamin C — Scurvy", "Vitamin D — Rickets", "Vitamin B12 — Anaemia", "Vitamin K — Blood clotting issues"], "e": "Vitamin deficiencies lead to specific health conditions."},
        {"q": "Match each country with its capital: Nigeria, Ghana, Kenya, Egypt, South Africa", "a": ["Nigeria — Abuja", "Ghana — Accra", "Kenya — Nairobi", "Egypt — Cairo", "South Africa — Pretoria"], "e": "Each country has a designated capital city."},
        {"q": "Match each force with its effect: Friction, Gravity, Magnetic, Elastic, Tension", "a": ["Friction — Opposes motion", "Gravity — Pulls objects down", "Magnetic — Attracts metals", "Elastic — Restores shape", "Tension — Pulls along a string"], "e": "Forces cause changes in the motion or shape of objects."},
        {"q": "Match each tissue type with its location: Epithelial, Muscle, Nervous, Connective, Blood", "a": ["Epithelial — Skin surface", "Muscle — Arms and legs", "Nervous — Brain and nerves", "Connective — Bones and tendons", "Blood — Circulatory system"], "e": "The body has four main tissue types with distinct locations."},
        {"q": "Match each literary device with its example: Metaphor, Simile, Alliteration, Personification, Hyperbole", "a": ["Metaphor — Time is money", "Simile — Brave as a lion", "Alliteration — Peter Piper", "Personification — Wind whispered", "Hyperbole — A million times"], "e": "Literary devices enhance writing through figurative language."},
    ],
    "ordering": [
        {"q": "Arrange the steps of the scientific method in the correct order.", "a": ["1. Observation", "2. Hypothesis", "3. Experiment", "4. Analysis", "5. Conclusion"], "e": "The scientific method follows a logical sequence from observation to conclusion."},
        {"q": "Arrange these stages of matter from lowest to highest energy.", "a": ["1. Solid", "2. Liquid", "3. Gas", "4. Plasma"], "e": "Energy increases as particles move more freely between states."},
        {"q": "Arrange the layers of the Earth from outermost to innermost.", "a": ["1. Crust", "2. Mantle", "3. Outer Core", "4. Inner Core"], "e": "The Earth has four main layers with increasing temperature toward the centre."},
        {"q": "Arrange these events in chronological order: World War I, Discovery of DNA, Moon Landing, Industrial Revolution, World War II", "a": ["1. Industrial Revolution", "2. World War I", "3. Discovery of DNA", "4. World War II", "5. Moon Landing"], "e": "These events span from the 18th century to the 20th century."},
        {"q": "Arrange the following food chain from producer to top consumer.", "a": ["1. Grass", "2. Grasshopper", "3. Frog", "4. Snake", "5. Eagle"], "e": "Energy flows from producers through primary to tertiary consumers."},
        {"q": "Arrange these body systems from simplest to most complex in terms of organ count.", "a": ["1. Integumentary (skin)", "2. Skeletal", "3. Muscular", "4. Nervous", "5. Digestive"], "e": "Systems vary in complexity based on the number of organs involved."},
        {"q": "Arrange the planets by size from smallest to largest: Jupiter, Mars, Venus, Mercury, Earth", "a": ["1. Mercury", "2. Mars", "3. Venus", "4. Earth", "5. Jupiter"], "e": "Mercury is the smallest planet; Jupiter is the largest."},
        {"q": "Arrange these numbers in ascending order: 3/4, 1/2, 2/3, 1/4, 5/6", "a": ["1. 1/4", "2. 1/2", "3. 2/3", "4. 3/4", "5. 5/6"], "e": "Converting to decimals: 0.25, 0.5, 0.667, 0.75, 0.833."},
        {"q": "Arrange the steps of mitosis in the correct order.", "a": ["1. Prophase", "2. Metaphase", "3. Anaphase", "4. Telophase"], "e": "Mitosis divides a cell into two identical daughter cells."},
        {"q": "Arrange these units of measurement from smallest to largest: kilometre, centimetre, millimetre, metre", "a": ["1. Millimetre", "2. Centimetre", "3. Metre", "4. Kilometre"], "e": "Metric units scale by powers of 10."},
    ],
    "image": [
        {"q": "Identify the organ shown in the diagram that is responsible for pumping blood.", "a": ["Heart"], "e": "The heart is a muscular organ that pumps blood through the circulatory system."},
        {"q": "From the labelled diagram of a leaf, identify the part where photosynthesis primarily occurs.", "a": ["Mesophyll", "Chloroplast"], "e": "Mesophyll cells contain chloroplasts where photosynthesis takes place."},
        {"q": "Study the diagram of the water cycle. What process is labelled 'A' where water vapour rises and cools?", "a": ["Condensation"], "e": "Condensation occurs when water vapour cools and forms clouds."},
        {"q": "Examine the diagram of an atom. What part is found in the centre of the atom?", "a": ["Nucleus"], "e": "The nucleus contains protons and neutrons at the centre of the atom."},
        {"q": "Look at the diagram of the digestive system. Which organ breaks down food using acid?", "a": ["Stomach"], "e": "The stomach uses hydrochloric acid and enzymes to break down food."},
        {"q": "Identify the type of rock shown in the image with visible layers or strata.", "a": ["Sedimentary rock"], "e": "Sedimentary rocks form in layers over time from deposited sediments."},
        {"q": "From the diagram of the solar system, which planet is shown with visible rings?", "a": ["Saturn"], "e": "Saturn is famous for its prominent ring system made of ice and rock particles."},
        {"q": "Study the circuit diagram. What component is used to resist the flow of current?", "a": ["Resistor"], "e": "A resistor limits current flow in an electrical circuit."},
        {"q": "Examine the map showing tectonic plate boundaries. What type of boundary causes earthquakes?", "a": ["Convergent boundary", "Transform boundary", "Plate boundary"], "e": "Earthquakes occur at all types of plate boundaries where plates interact."},
        {"q": "Identify the structure labelled 'X' in the diagram of a flower that contains the ovules.", "a": ["Ovary"], "e": "The ovary is part of the pistil and contains ovules that develop into seeds."},
    ],
}


class Command(BaseCommand):
    help = "Seed questions for all non-MCQ types (True/False, Fill-blank, Essay, Matching, Ordering, Image)"

    def handle(self, *args, **options):
        subjects = list(Subject.objects.all())
        if not subjects:
            self.stderr.write("No subjects found. Run 'python manage.py seed' first.")
            return

        created_total = 0
        skipped_total = 0
        for q_type, questions in QUESTION_DATA.items():
            random.shuffle(questions)
            for i, data in enumerate(questions):
                subject = subjects[i % len(subjects)]
                if Question.objects.filter(question_text=data["q"], school=subject.school).exists():
                    skipped_total += 1
                    continue
                Question.objects.create(
                    question_text=data["q"],
                    question_type=q_type,
                    options=[],
                    correct_answer=data["a"],
                    explanation=data["e"],
                    marks=random.choice([2, 3, 5]) if q_type == "essay" else random.choice([1, 2]),
                    difficulty=random.choice(["easy", "medium", "hard"]),
                    subject=subject,
                    topic=None,
                    tags=[q_type.replace("_", "-")],
                    status="published",
                    school=subject.school,
                )
                created_total += 1
            self.stdout.write(f"  {q_type}: {len(questions)} questions processed")

        self.stdout.write(self.style.SUCCESS(f"\nDone — {created_total} created, {skipped_total} skipped"))
