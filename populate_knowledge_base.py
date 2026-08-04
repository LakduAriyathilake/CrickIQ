import os

knowledge_base = {
    "dls_method": """The Duckworth-Lewis-Stern (DLS) method is used to calculate a fair target score
when a cricket match is interrupted, delayed, or rained out and overs have to be
reduced. If rain stops play and the match is shortened, DLS recalculates a revised
target for the team batting second, rather than simply using the original run rate.
It works by tracking two resources a team has at any point in an innings: the
number of overs remaining and the number of wickets in hand. This means a rain
delay does not always halve the target if half the overs are lost, since wickets
in hand matter too. DLS replaced older, simpler methods because it accounts for
both overs and wickets together when a match is washed out or cut short.""",

    "powerplay_rules": """In T20 cricket, the powerplay refers to the first 6 overs of each innings, during
which fielding restrictions apply. Only two fielders are allowed outside the 30-yard
circle during this period, which forces the fielding team to keep more players
close to the batter. This typically makes it easier for the batting side to score
boundaries early in the innings. After the powerplay ends, up to five fielders can
be placed outside the circle, making it harder to find gaps and generally slowing
the run rate until the death overs.""",

    "super_over": """A super over is used to break a tie in a T20 match that finishes level after both
teams have batted their full innings. Each team bats one additional over with two
batters and one bowler, and whichever team scores more runs in that over wins the
match. If the super over itself ends in a tie, another super over is played,
continuing until a winner is decided. A team can only use bowlers who bowled fewer
than four overs in the main match to bowl the super over, and typically cannot use
a batter who was already dismissed in the main innings.""",

    "reverse_swing": """Reverse swing is a bowling technique where an old cricket ball, usually after 20
or more overs of wear, starts to swing in the opposite direction to what its
shine and seam position would normally suggest. It typically requires one side of
the ball to be kept rough and dry while the other side is kept smoother, creating
an uneven aerodynamic effect at higher bowling speeds. It's most associated with
fast bowlers in the latter half of an innings, particularly in subcontinent
conditions where pitches offer less conventional seam movement.""",

    "dismissal_types": """A batter can be dismissed in several ways in cricket. Bowled means the ball hits
the stumps directly from the bowler's delivery. Caught means a fielder catches
the ball before it touches the ground after the batter hits it. LBW (leg before
wicket) means the ball would have hit the stumps but was blocked by the batter's
leg or body instead of the bat. Run out happens when a fielder breaks the stumps
with the ball while the batter is outside their crease attempting a run. Stumped
is similar but specifically when the wicketkeeper breaks the stumps while the
batter is out of their crease, usually after missing a shot.""",

    "drs_review_system": """The Decision Review System (DRS) allows teams to challenge an on-field umpire's
decision using technology such as ball-tracking, ultra-edge (sound-based edge
detection), and replays. Each team is typically given a limited number of
unsuccessful reviews per innings, usually two in international cricket. If a
review is upheld (the original decision is overturned), the team does not lose
that review. For LBW decisions specifically, the ball-tracking prediction must
show the ball hitting the stumps within the marked zone for the decision to be
overturned in the batter's favor when reviewing an out decision, or in the
bowler's favor when reviewing a not-out decision.""",

    "no_ball_and_free_hit": """A no-ball is called by the umpire when the bowler oversteps the popping crease,
bowls a delivery above waist height without it being a legal bouncer, or breaks
other specific delivery rules. A no-ball results in one extra run to the batting
team and the ball must be re-bowled. In limited-overs cricket, a no-ball is
usually followed by a free hit, meaning the batter cannot be dismissed on the
next delivery except by run out, regardless of how they play the shot.""",

    "follow_on_rule": """The follow-on is a rule specific to Test and first-class multi-day cricket. If
the team batting second is dismissed for significantly fewer runs than the team
that batted first (typically at least 200 runs behind in a Test match), the team
that batted first has the option to enforce the follow-on, making the team that
batted second bat again immediately instead of the side that led taking their
turn to bat. This rule does not apply in limited-overs formats like ODIs or T20s,
which only have one innings per side.""",

    "wide_ball_rule": """A wide is called when the ball passes too far from the batter, outside the
reach of a normal cricket shot, based on marked guidelines on the pitch. A wide
results in one extra run awarded to the batting team, and the delivery must be
bowled again since it does not count as one of the over's six legal balls. In
limited-overs cricket, umpires tend to apply wide restrictions more strictly than
in Test cricket, especially regarding deliveries down the leg side.""",

    "toss_and_its_impact": """At the start of a cricket match, the two captains take part in a coin toss to
decide which team bats or fields first. The winning captain chooses based on
factors like pitch conditions, weather, and format. In conditions expected to
assist bowlers early on (such as overcast weather or a fresh, seam-friendly
pitch), teams often choose to bowl first. In matches where dew is expected later
in the evening (common in day-night matches in the subcontinent), teams often
prefer to bowl first to avoid batting on a wet, harder-to-grip ball later in
their innings.""",

    "types_of_deliveries": """Bowlers use different types of deliveries to deceive batters. A yorker is aimed
at the batter's feet or the base of the stumps, making it hard to get under the
ball for a big shot. A bouncer is a short, fast delivery aimed to rise toward
the batter's chest or head. Spin bowlers use variations like the googly (a
leg-spinner's delivery that turns the opposite way to a normal leg break) and
the doosra (an off-spinner's delivery that turns away from a right-handed
batter, opposite to a normal off break).""",

    "powerplay_vs_death_overs": """Cricket innings in T20 and ODI matches are broadly split into phases with
different strategic priorities. The powerplay (the first 6 overs in T20, first
10 in ODIs) favors aggressive batting due to fielding restrictions. The middle
overs typically see more measured batting, focused on rotating strike and
building a platform, since fielding restrictions ease. The death overs (the
final few overs of an innings, from around over 15 onward in T20 cricket) often
see the highest scoring rates as batters look to maximize runs before the
innings ends, and bowlers focus on yorkers and variations to limit boundaries.""",

 "mankad_dismissal": """A Mankad is a run out of the non-striking batter, carried out by the bowler
before delivering the ball, when that batter has left their crease early to gain
a head start on a run. It is named after Indian bowler Vinoo Mankad, who first
used the method in a Test match in 1947. Once considered controversial and
against the "spirit of the game," it is now recognized simply as a standard form
of run out under the official laws of cricket, and is entirely legal at any
point before the bowler releases the ball.""",

    "hit_wicket": """A batter is given out hit wicket if they accidentally dislodge their own
stumps with their bat, body, or equipment while playing a shot or setting off
for a run. This can happen if the bat touches the stumps during a backswing or
follow-through, or if the batter steps back onto the stumps. It is a relatively
rare dismissal and counts against the batter even though no fielder or bowler
action caused it directly.""",

    "obstructing_the_field": """A batter can be given out for obstructing the field if they deliberately
interfere with a fielder's attempt to field the ball, effect a run out, or take
a catch. This includes deliberately blocking a throw with the body or bat, or
verbally distracting a fielder. It is a rare dismissal since it requires the
umpire to judge the batter's action as intentional rather than accidental.""",

    "retired_hurt_and_retired_out": """A batter who leaves the field due to injury or illness during their innings is
recorded as 'retired hurt' and can typically resume batting later in the innings
if they recover, usually resuming at the fall of the next wicket. If a batter
retires for any reason other than injury or illness, and without the umpire's
consent, it is instead recorded as 'retired out,' and unlike retired hurt, they
are not permitted to return to bat later in the innings.""",

    "net_run_rate": """Net Run Rate (NRR) is a statistic used to separate teams that finish level on
points in a tournament's group stage or standings. It is calculated as the
average number of runs a team scores per over across all their matches, minus
the average number of runs per over they concede to opponents. A higher net run
rate reflects a team that has generally outscored opponents by a wider margin
across the tournament, and it often decides which teams advance when points
are tied.""",

    "maiden_over": """A maiden over is an over in which the bowler concedes no runs at all, meaning
no runs are scored off the bat and no extras such as wides or no-balls are
conceded either. It is considered a strong bowling performance, since it puts
scoring pressure on the batting side, and is more common in longer formats than
in T20 cricket, where boundary-focused batting makes maidens rarer.""",

    "concussion_substitute": """A concussion substitute is a like-for-like replacement player allowed onto the
field when a player suffers a suspected concussion during a match, such as being
struck on the head by the ball. The replacement must be of a similar playing
type (for example, a bowler replaced by a bowler) and is subject to approval by
the match referee before being allowed to take the field.""",

    "over_rate_penalties": """Teams are required to bowl their allotted overs within a set time limit during
a match. If a fielding team falls behind this required over rate, they can face
penalties, which vary by competition and format but commonly include fines for
players and team management. In some limited-overs formats, a slow over rate can
also result in fielding restrictions being imposed on the fielding team for the
remaining overs of the innings, similar to powerplay restrictions.""",
}

def write_knowledge_files(folder="knowledge_base"):
    os.makedirs(folder, exist_ok=True)
    for filename, content in knowledge_base.items():
        filepath = os.path.join(folder, f"{filename}.txt")
        with open(filepath, "w") as f:
            f.write(content.strip())
        print(f"Written: {filepath}")
    print(f"\nTotal files written: {len(knowledge_base)}")

if __name__ == "__main__":
    write_knowledge_files()