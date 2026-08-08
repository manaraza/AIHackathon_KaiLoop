# Kai Loop — Pitch Speaker Notes

Target length: ~3.5–4 minutes. Timing cues are guides, not a script to read robotically — practice until it sounds like you, not like you're reading.

---

## Hook (0:00–0:15)

> Right now, in New Zealand, one in five households don't have enough food to eat.
>
> At the exact same time, on farms across the country, perfectly good produce is being thrown away — not because it's spoiled, but because an apple is too small, or a carrot forked the wrong way.
>
> Those two facts are happening simultaneously, in the same country, and they're connected. That's what Kai Loop fixes.

**Delivery note:** pause after "enough food to eat." Let the contrast between the two facts land before moving on — don't rush the connection.

---

## Problem (0:15–0:55)

> Food waste isn't one problem, it's three, stacked across the whole supply chain. Twenty-two percent of it happens right at the farm, from produce that's cosmetically "imperfect" but completely edible. Sixteen percent happens in restaurants and cafes, from over-portioned or unpopular dishes that come back to the kitchen barely touched. And more is lost at retail — stock that's still good but sitting too close to its expiry date to sell in time.
>
> It matters at a scale that's easy to say and hard to picture: food waste causes eight to ten percent of global greenhouse gas emissions. That's more than the entire aviation industry. And it's happening while, as I said, one in five Kiwi households are going without.

**Delivery note:** the aviation comparison is your most quotable line — slow down slightly and let it sit.

---

## Insight (0:55–1:15)

> Here's why this hasn't been solved already: waste gets caught too late, and each part of the chain is blind to the others. The farmer doesn't know what the kitchen is over-portioning. The kitchen doesn't know what's about to expire on the retail shelf. Everyone's managing their own waste in isolation, and good food keeps slipping through the cracks in between.
>
> So the fix isn't one clever trick — it's connecting the three blind spots into one loop.

---

## Solution (1:15–2:45)

> That's Kai Loop: three modules, one shared purpose — catch food before it becomes waste, at the moment it's still avoidable.
>
> **SecondCrop** is the farm-side module. Take a photo of produce, and a trained image model grades it — Grade A goes to retail, Grade B gets flagged for processing, Grade C routes straight to rescue through KiwiHarvest for redistribution. This is the one we built fully end to end, not just mocked up — it's a real MobileNetV2 model we trained ourselves, and it actually works. *(Cue: live demo here — grade one photo live if you have the time slot for it. If you have multiple pieces of produce, show the batch mode: it detects and grades every item in one photo, not just one at a time — because no farmer is going to photograph fruit one at a time.)*
>
> **ScrapSense** is the kitchen-side module. A photo of a plate after a meal gets scored for how much food came back uneaten. Once a dish is logged a few times, if it's consistently coming back with food left on it, the system flags it as over-portioned and suggests a specific cut — so kitchens can right-size portions before more food gets wasted, not after.
>
> **Second Serve** is the retail-side module. No photo needed here — it works straight off the inventory data a store already has: product, expiry date, quantity. Anything within a day or two of expiring gets flagged for markdown or rescue automatically.
>
> All three feed the same place: KiwiHarvest, so surplus that's caught anywhere in the chain gets redistributed to people who need it, instead of landfill.
>
> To be upfront about where we are: SecondCrop is a fully working prototype with a real trained model. ScrapSense and Second Serve are working, tested, rule-based versions — not fake demos, genuinely functional — but not yet trained on their own data the way SecondCrop is. That's the honest state of a hackathon build, and it's also exactly our roadmap.

**Delivery note:** the parenthetical demo cue is for you, not the audience — cut it if you're not doing a live demo in this slot.

---

## Financial & practical viability (2:45–3:30)

> This isn't just technically feasible, it's cheap to build and cheap to run. The whole stack is open-source — React, FastAPI, a MobileNetV2 model we trained for free on Google Colab in under 40 minutes. There's no proprietary API cost, and the model is small enough to run on a basic server, not a GPU cluster. Adoption cost for a farm, kitchen, or store is close to zero: no new hardware, no barcode scanners, no IoT sensors — just a phone camera they already have, or spreadsheet data they already keep.
>
> And it pays for itself on both sides. Farms recover value from produce that was heading for a total write-off. Kitchens cut food cost directly, because over-portioning is wasted money before it's wasted food. Retailers convert a near-total loss on expiring stock into a markdown sale instead of zero. None of this requires the businesses to change how they operate — it requires them to take a photo they weren't taking before.
>
> The real dependency is partnership, not technology: this only closes the loop with an organization like KiwiHarvest actually handling redistribution logistics on the other end. We're not building a rescue operation, we're building the layer that tells an existing one where to look.

---

## Close / Call to action (3:30–3:50)

> In this hackathon, we proved the hardest part first: a real, trained model, grading real produce, end to end, with the other two modules built and working alongside it. The architecture already supports all three feeding one loop.
>
> What we're asking for isn't hypothetical — it's the next dataset. A supermarket photo shoot gives SecondCrop a true third grade. More plate photos train ScrapSense properly. That's it. That's the gap between what you're looking at today and something a farm, a kitchen, or a store could actually use tomorrow.

**Delivery note:** end on "tomorrow" — don't add a trailing "thank you, questions" tag onto the same breath. Let it land, then stop.

---

## Anticipated judge questions (prep, not part of the script)

- **"Why not just use a bigger/better model?"** — Time and data, not ambition. MobileNetV2 was the right size to train to convergence in a hackathon window; a bigger model needs more data and more training time than we had, not a fundamentally different approach.
- **"What happens to Grade B produce right now, since you don't have real training data for it?"** — The model is currently binary (fresh/rotten). Grade B is a proxy: any score in the uncertain middle range gets flagged for manual review rather than guessed at. That's a deliberate, honest placeholder, not a hidden gap.
- **"How do you know ScrapSense/Second Serve's numbers are meaningful if they're heuristics, not trained models?"** — They're calibrated against real photos and real scenarios, not arbitrary. We tested and tuned both against actual data during the hackathon and can show the calibration process if asked.
- **"What's the actual cost to run this at scale?"** — Inference is cheap (small CPU-friendly model), so cost scales roughly with photo volume, not user count — a single-digit-dollars/month hosting bill covers early pilot usage.
