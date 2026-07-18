import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.papers.models import ExamPaper, ExamPaperQuestion
from apps.questions.models import Question
from apps.schools.models import School
from apps.subjects.models import Subject, Topic

User = get_user_model()

SUBJECTS_DATA = {
    "Mathematics": {
        "topics": ["Algebra", "Geometry", "Trigonometry", "Statistics", "Calculus"],
        "questions": [
            ("Simplify: 3x + 5x - 2x", ["mcq", "6x", "8x", "4x", "10x"], ["6x"], "easy", 1, "Combine like terms by adding coefficients."),
            ("If x + 5 = 12, find x", ["mcq", "5", "7", "12", "17"], ["7"], "easy", 1, "Subtract 5 from both sides."),
            ("What is the area of a circle with radius 7cm? (Use pi = 22/7)", ["mcq", "154 cm²", "144 cm²", "148 cm²", "156 cm²"], ["154 cm²"], "medium", 2, "Area = pi × r² = 22/7 × 49 = 154"),
            ("Solve: 2x² - 8 = 0", ["mcq", "x = 2", "x = 4", "x = ±2", "x = ±4"], ["x = ±2"], "medium", 2, "2x² = 8, x² = 4, x = ±2"),
            ("The sum of angles in a triangle is", ["mcq", "90°", "180°", "270°", "360°"], ["180°"], "easy", 1, "Fundamental property of triangles."),
            ("Find the derivative of x³ + 2x", ["mcq", "3x² + 2", "3x² + x", "x² + 2", "3x + 2"], ["3x² + 2"], "medium", 2, "Apply power rule: d/dx(xⁿ) = nxⁿ⁻¹"),
            ("What is the value of sin 30°?", ["mcq", "0.5", "0.866", "1", "0"], ["0.5"], "easy", 1, "Standard trigonometric value."),
            ("The mean of 2, 4, 6, 8, 10 is", ["mcq", "5", "6", "7", "8"], ["6"], "easy", 1, "Mean = sum of values / number of values = 30/5 = 6"),
            ("Factorize: x² - 9", ["mcq", "(x-3)(x+3)", "(x-9)(x+1)", "(x-3)²", "(x+3)²"], ["(x-3)(x+3)"], "medium", 2, "Difference of two squares: a²-b² = (a-b)(a+b)"),
            ("The hypotenuse of a right triangle with sides 3 and 4 is", ["mcq", "5", "6", "7", "12"], ["5"], "easy", 1, "Pythagoras theorem: 3² + 4² = 9 + 16 = 25, √25 = 5"),
        ],
    },
    "English Language": {
        "topics": ["Grammar", "Comprehension", "Vocabulary", "Essay Writing", "Literature"],
        "questions": [
            ("Choose the correct pronoun: '___ and I went to the market.'", ["mcq", "Me", "Myself", "I", "We"], ["I"], "easy", 1, "Subject pronoun is used when it's the subject of the verb."),
            ("Which word is a synonym of 'abundant'?", ["mcq", "Scarce", "Plentiful", "Limited", "Rare"], ["Plentiful"], "easy", 1, "Abundant means existing in large quantities."),
            ("Identify the verb in: 'The cat sat on the mat.'", ["mcq", "cat", "sat", "mat", "on"], ["sat"], "easy", 1, "The verb describes the action performed."),
            ("The past tense of 'go' is", ["mcq", "goed", "went", "gone", "going"], ["went"], "easy", 1, "Go is an irregular verb."),
            ("Which is a complex sentence?", ["mcq", "I went home.", "I went home and slept.", "Although it rained, we went out.", "She likes tea."], ["Although it rained, we went out."], "medium", 2, "A complex sentence has an independent clause and a dependent clause."),
            ("Choose the correct article: '___ sun rises in the east.'", ["mcq", "A", "An", "The", "No article"], ["The"], "easy", 1, "We use 'the' for unique objects."),
            ("The plural of 'child' is", ["mcq", "childs", "childen", "children", "child's"], ["children"], "easy", 1, "Child has an irregular plural form."),
            ("Which word is an antonym of 'brave'?", ["mcq", "Bold", "Courageous", "Cowardly", "Fearless"], ["Cowardly"], "easy", 1, "Brave means showing courage, cowardly means lacking courage."),
            ("'She has been studying for three hours.' The underlined verb is in", ["mcq", "Simple present", "Present continuous", "Present perfect continuous", "Past tense"], ["Present perfect continuous"], "medium", 2, "Has been + verb-ing indicates present perfect continuous."),
            ("Identify the adjective: 'The tall man wore a blue shirt.'", ["mcq", "man", "tall", "wore", "shirt"], ["tall"], "easy", 1, "Adjectives describe nouns."),
        ],
    },
    "Biology": {
        "topics": ["Cell Biology", "Genetics", "Ecology", "Human Anatomy", "Evolution"],
        "questions": [
            ("The powerhouse of the cell is the", ["mcq", "Nucleus", "Ribosome", "Mitochondria", "Golgi body"], ["Mitochondria"], "easy", 1, "Mitochondria produces ATP through cellular respiration."),
            ("DNA stands for", ["mcq", "Deoxyribonucleic Acid", "Dioxyribonucleic Acid", "Deoxyribose Nucleic Acid", "Deoxyribonuclear Acid"], ["Deoxyribonucleic Acid"], "easy", 1, "DNA carries genetic information."),
            ("Which organelle is responsible for photosynthesis?", ["mcq", "Mitochondria", "Chloroplast", "Ribosome", "Vacuole"], ["Chloroplast"], "easy", 1, "Chloroplasts contain chlorophyll for photosynthesis."),
            ("The basic unit of life is the", ["mcq", "Organ", "Tissue", "Cell", "Organism"], ["Cell"], "easy", 1, "Cell theory states that the cell is the basic unit of life."),
            ("Which blood group is the universal donor?", ["mcq", "A+", "B+", "AB+", "O-"], ["O-"], "medium", 2, "O- has no antigens and can be given to anyone."),
            ("The process by which cells divide to form two identical daughter cells is", ["mcq", "Meiosis", "Mitosis", "Binary fission", "Budding"], ["Mitosis"], "medium", 2, "Mitosis produces two identical cells for growth and repair."),
            ("Which of these is NOT a function of the liver?", ["mcq", "Detoxification", "Bile production", "Insulin production", "Glycogen storage"], ["Insulin production"], "medium", 2, "Insulin is produced by the pancreas, not the liver."),
            ("The outer layer of the skin is called", ["mcq", "Dermis", "Epidermis", "Hypodermis", "Subcutis"], ["Epidermis"], "easy", 1, "The epidermis is the outermost protective layer."),
            ("Fertilization in humans occurs in the", ["mcq", "Uterus", "Ovary", "Fallopian tube", "Vagina"], ["Fallopian tube"], "medium", 2, "The egg meets sperm in the fallopian tube."),
            ("Which factor is NOT density-dependent?", ["mcq", "Predation", "Disease", "Natural disasters", "Competition"], ["Natural disasters"], "medium", 2, "Natural disasters are density-independent factors."),
        ],
    },
    "Chemistry": {
        "topics": ["Atomic Structure", "Chemical Bonding", "Acids and Bases", "Organic Chemistry", "Stoichiometry"],
        "questions": [
            ("The atomic number of carbon is", ["mcq", "4", "6", "8", "12"], ["6"], "easy", 1, "Carbon has 6 protons in its nucleus."),
            ("Water has the chemical formula", ["mcq", "HO", "H₂O", "H₂O₂", "H₃O"], ["H₂O"], "easy", 1, "Water consists of 2 hydrogen atoms and 1 oxygen atom."),
            ("The pH of pure water at 25°C is", ["mcq", "0", "7", "14", "1"], ["7"], "easy", 1, "Pure water is neutral with pH 7."),
            ("Which gas is released when hydrochloric acid reacts with calcium carbonate?", ["mcq", "Oxygen", "Hydrogen", "Carbon dioxide", "Nitrogen"], ["Carbon dioxide"], "medium", 2, "CaCO₃ + 2HCl → CaCl₂ + H₂O + CO₂"),
            ("The number of electrons in a sodium atom is", ["mcq", "10", "11", "12", "23"], ["11"], "easy", 1, "Sodium has atomic number 11, so 11 electrons."),
            ("Covalent bonds involve", ["mcq", "Transfer of electrons", "Sharing of electrons", "Loss of electrons", "Gain of electrons"], ["Sharing of electrons"], "easy", 1, "In covalent bonds, atoms share electron pairs."),
            ("The chemical formula for sulfuric acid is", ["mcq", "HCl", "HNO₃", "H₂SO₄", "H₃PO₄"], ["H₂SO₄"], "medium", 2, "Sulfuric acid is a strong diprotic acid."),
            ("Which is an organic compound?", ["mcq", "NaCl", "H₂O", "CH₄", "CaO"], ["CH₄"], "easy", 1, "Organic compounds contain carbon-hydrogen bonds."),
            ("The mass of one mole of water is", ["mcq", "1 g", "18 g", "36 g", "2 g"], ["18 g"], "medium", 2, "Molar mass = 2(1) + 16 = 18 g/mol"),
            ("An acid turns litmus paper", ["mcq", "Blue", "Red", "Green", "Yellow"], ["Red"], "easy", 1, "Acids turn blue litmus paper red."),
        ],
    },
    "Physics": {
        "topics": ["Newtonian Mechanics", "Electricity", "Waves", "Thermodynamics", "Optics"],
        "questions": [
            ("Newton's first law is also known as the law of", ["mcq", "Acceleration", "Inertia", "Action-reaction", "Gravity"], ["Inertia"], "easy", 1, "An object remains at rest or in uniform motion unless acted upon."),
            ("The SI unit of force is the", ["mcq", "Joule", "Watt", "Newton", "Pascal"], ["Newton"], "easy", 1, "1 Newton = 1 kg·m/s²"),
            ("The speed of light in a vacuum is approximately", ["mcq", "3 × 10⁶ m/s", "3 × 10⁸ m/s", "3 × 10¹⁰ m/s", "3 × 10⁴ m/s"], ["3 × 10⁸ m/s"], "easy", 1, "c = 299,792,458 m/s ≈ 3 × 10⁸ m/s"),
            ("Ohm's law states that V = ", ["mcq", "IR", "I/R", "R/I", "I²R"], ["IR"], "easy", 1, "Voltage equals current times resistance."),
            ("The frequency of a wave is measured in", ["mcq", "Metres", "Hertz", "Seconds", "Newtons"], ["Hertz"], "easy", 1, "1 Hz = 1 cycle per second."),
            ("Energy cannot be created or destroyed. This is the law of", ["mcq", "Conservation of momentum", "Conservation of energy", "Thermodynamics", "Inertia"], ["Conservation of energy"], "medium", 2, "Energy can only be converted from one form to another."),
            ("The resistance of a pure conductor increases with", ["mcq", "Decrease in temperature", "Increase in temperature", "Decrease in length", "Increase in cross-section"], ["Increase in temperature"], "medium", 2, "More temperature means more atomic vibrations impeding electron flow."),
            ("A concave mirror can produce", ["mcq", "Only virtual images", "Only real images", "Both real and virtual images", "No images"], ["Both real and virtual images"], "medium", 2, "Concave mirrors can form real or virtual images depending on object distance."),
            ("The SI unit of electric current is the", ["mcq", "Volt", "Ohm", "Ampere", "Watt"], ["Ampere"], "easy", 1, "1 Ampere = 1 Coulomb per second."),
            ("The phenomenon of splitting of white light into seven colours is called", ["mcq", "Reflection", "Refraction", "Dispersion", "Diffraction"], ["Dispersion"], "medium", 2, "A prism splits white light into its component colours."),
        ],
    },
}

DEFAULT_SCHOOLS = [
    {"name": "Greenfield Academy", "address": "12 Education Road, Lagos", "phone": "+234 801 234 5678"},
    {"name": "ABC Collage", "address": "45 Academy Street, Abuja", "phone": "+234 802 345 6789"},
]


class Command(BaseCommand):
    help = "Seed the database with sample data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--school",
            type=str,
            default="all",
            help="School name to seed (or 'all' for all schools). Default: all",
        )

    def seed_school(self, school):
        self.stdout.write(f"\n  Seeding: {school.name}")

        # Admin user for this school
        admin_email = f"admin@{school.name.lower().replace(' ', '')}.com"
        admin, created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                "first_name": "Admin",
                "last_name": school.name.split()[0],
                "role": "admin",
                "is_staff": True,
                "is_superuser": False,
                "school": school,
            },
        )
        if created:
            admin.set_password("admin123")
        if admin.school != school:
            admin.school = school
        admin.role = "admin"
        admin.is_superuser = False
        admin.is_staff = True
        admin.save()

        # Teacher user for this school
        teacher_email = f"teacher@{school.name.lower().replace(' ', '')}.com"
        teacher, created = User.objects.get_or_create(
            email=teacher_email,
            defaults={
                "first_name": "Amina",
                "last_name": "Okafor",
                "role": "teacher",
                "school": school,
            },
        )
        if created:
            teacher.set_password("teacher123")
        if teacher.school != school:
            teacher.school = school
        teacher.save()

        # Subjects, Topics, Questions
        question_count = 0
        topic_count = 0
        for subject_name, data in SUBJECTS_DATA.items():
            subject, _ = Subject.objects.get_or_create(
                name=subject_name,
                school=school,
                defaults={"created_by": admin},
            )
            for topic_name in data["topics"]:
                topic, created = Topic.objects.get_or_create(
                    name=topic_name,
                    subject=subject,
                )
                if created:
                    topic_count += 1

            topics = list(subject.topics.all())
            for q_data in data["questions"]:
                text, options, answer, difficulty, marks, explanation = q_data
                if Question.objects.filter(question_text=text, school=school).exists():
                    continue
                Question.objects.create(
                    question_text=text,
                    question_type="mcq",
                    options=options,
                    correct_answer=answer,
                    explanation=explanation,
                    marks=marks,
                    difficulty=difficulty,
                    subject=subject,
                    topic=random.choice(topics) if topics else None,
                    tags=[subject_name.lower(), difficulty],
                    status=random.choice(["published", "published", "draft"]),
                    school=school,
                    created_by=random.choice([admin, teacher]),
                )
                question_count += 1

        # Exam paper
        math = Subject.objects.get(name="Mathematics", school=school)
        paper, created = ExamPaper.objects.get_or_create(
            title="Mathematics First Term Examination",
            school=school,
            defaults={
                "subject": math,
                "class_name": "JSS 3",
                "duration_minutes": 60,
                "total_marks": 20,
                "academic_session": "2025/2026",
                "term": "First Term",
                "status": "draft",
                "created_by": admin,
            },
        )
        if created:
            math_questions = list(Question.objects.filter(subject=math, school=school)[:10])
            for i, q in enumerate(math_questions, 1):
                ExamPaperQuestion.objects.get_or_create(
                    exam_paper=paper,
                    question=q,
                    defaults={"order": i},
                )
            self.stdout.write(f"    Paper: {paper.title} with {len(math_questions)} questions")

        # Assign 3 subjects to teacher
        teacher_subjects = Subject.objects.filter(
            name__in=["Mathematics", "English Language", "Biology"], school=school
        )
        teacher.subjects.set(teacher_subjects)

        self.stdout.write(f"    Admin: {admin.email} / admin123")
        self.stdout.write(f"    Teacher: {teacher.email} / teacher123")
        self.stdout.write(f"    Subjects: 5 | Topics: {topic_count} | Questions: {question_count}")
        return admin, teacher

    def handle(self, *args, **options):
        school_name = options["school"]

        # Create super admin user (one global super admin)
        super_email = "superadmin@example.com"
        super_admin, created = User.objects.get_or_create(
            email=super_email,
            defaults={
                "first_name": "Super",
                "last_name": "Admin",
                "role": "super_admin",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            super_admin.set_password("superadmin123")
        super_admin.role = "super_admin"
        super_admin.is_superuser = True
        super_admin.is_staff = True
        super_admin.save()
        self.stdout.write(f"  Super Admin: {super_email} / superadmin123")

        if school_name == "all":
            schools = []
            for s_data in DEFAULT_SCHOOLS:
                school, _ = School.objects.get_or_create(
                    name=s_data["name"],
                    defaults={"address": s_data["address"], "phone": s_data["phone"]},
                )
                schools.append(school)
        else:
            school, _ = School.objects.get_or_create(
                name=school_name,
                defaults={"address": "", "phone": ""},
            )
            schools = [school]

        self.stdout.write("Seeding database...")
        for school in schools:
            self.seed_school(school)

        self.stdout.write(self.style.SUCCESS("\nDone! Database seeded successfully.\n"))
        self.stdout.write(f"  Super Admin: {super_email} / superadmin123")
        for school in schools:
            admin_email = f"admin@{school.name.lower().replace(' ', '')}.com"
            teacher_email = f"teacher@{school.name.lower().replace(' ', '')}.com"
            self.stdout.write(f"  {school.name}:")
            self.stdout.write(f"    Admin:    {admin_email} / admin123")
            self.stdout.write(f"    Teacher:  {teacher_email} / teacher123")
