from adx.agents import NDaysNCampaignsAgent
from adx.tier1_ndays_ncampaign_agent import Tier1NDaysNCampaignsAgent
from adx.adx_game_simulator import AdXGameSimulator
from adx.structures import Bid, Campaign, BidBundle, MarketSegment
from typing import Set, Dict
import random

class MyNDaysNCampaignsAgent(NDaysNCampaignsAgent):

    def __init__(self):
        # TODO: fill this in (if necessary)
        super().__init__()
        self.name = "__placeholder__"  # TODO: enter a name.

    def on_new_game(self) -> None:
        pass

    def get_ad_bids(self) -> Set[BidBundle]:
        bundles = set()
        #print(self.get_current_day(), len(self.get_active_campaigns()))
        #print("Quality score:", self.get_quality_score())

        # Scales from 1 to x for how much we care about quality score.
        quality_score_alpha = 1 - (self.get_current_day() * 0.02) # fewer days left --> bid less
        quality_score = self.get_quality_score()

        # quality_score_alpha_2 seems to not actually be helping!
        # if quality_score < 0.7:
        #     quality_score_alpha_2 = 1.2
        # elif quality_score < 0.5:
        #     quality_score_alpha_2 = 2
        # else:
        #     quality_score_alpha_2 = 1

        for campaign in self.get_active_campaigns():
            bids = set()
            days_left = campaign.end_day - self.get_current_day()
            reach_left = campaign.reach - self.get_cumulative_reach(campaign)
            budget_left = campaign.budget - self.get_cumulative_cost(campaign)

            campaign_segment = campaign.target_segment
            if reach_left <= 0 or budget_left <= 0:
                initial_bid = 0
            else:
                initial_bid = budget_left / reach_left

            days_left_alpha = 1 - (.05 * days_left) # more days left --> bid less
            percent_reach_left = reach_left / campaign.reach
            reach_alpha = (.1 * percent_reach_left) + .9 # more reach left --> bid more

            for segment in MarketSegment.all_segments():
                if not segment.issubset(campaign_segment):
                    continue

                # If a market segment is more specific, bid more, otherwise, bid less
                # (less supply means must bid more, in theory)
                if len(segment) == 2:   segment_specificity_alpha = .7
                else:                   segment_specificity_alpha = 1

                bid_per_item = 0.4 * initial_bid * segment_specificity_alpha * quality_score_alpha * days_left_alpha * reach_alpha #* quality_score_alpha_2

                bid_limit = budget_left
                bid = Bid(self, segment, bid_per_item, bid_limit)
                #print("bid per item:", bid_per_item)
                bids.add(bid)

            campaign_limit = budget_left
            bundle = BidBundle(campaign_id=campaign.uid, limit=campaign_limit, bid_entries=bids)
            bundles.add(bundle)
        return bundles


    def get_campaign_bids(self, campaigns_for_auction:  Set[Campaign]) -> Dict[Campaign, float]:
        # reverse auction - lower bids win!
        bids = {}
        for auction_campaign in campaigns_for_auction:
            initial_bid = auction_campaign.reach

            campaign_length = auction_campaign.end_day - auction_campaign.start_day # 0, 1, or 2
            campaign_alpha = 1 - .1 * campaign_length # we pay less for (prefer) longer campaigns

            if len(auction_campaign.target_segment) == 2:   specificity_alpha = 0.8
            else:                                           specificity_alpha = 1

            issubset_alpha = 1
            for my_campaign in self.get_active_campaigns():
                my_target_segment = my_campaign.target_segment
                auction_target_segment = auction_campaign.target_segment
                if my_target_segment.issubset(auction_target_segment) or auction_target_segment.issubset(my_target_segment):
                    issubset_alpha = 0.8
            # we pay less for (prefer) campaigns with similar market segments to our current campaigns
            # this is how we (theoretically) corner the market

            # alternative issubset_alpha calculator
            # num_related = 0
            # for my_campaign in self.get_active_campaigns():
            #     my_target_segment = my_campaign.target_segment
            #     auction_target_segment = auction_campaign.target_segment
            #     if my_target_segment.issubset(auction_target_segment) or auction_target_segment.issubset(my_target_segment):
            #         num_related += 1
            # if len(self.get_active_campaigns()) == 0:
            #     issubset_alpha = 1
            # else:
            #     issubset_alpha = 1 - 0.1 * (num_related / len(self.get_active_campaigns()))
            #     # we pay less for (prefer) campaigns with similar market segments as larger percentages of our current campaigns
            #     # this is how we (theoretically) corner the market

            bid_value = 0.4 * initial_bid * campaign_alpha * specificity_alpha * issubset_alpha
            bid_value = self.clip_campaign_bid(auction_campaign, bid_value)
            bids[auction_campaign] = bid_value

        return bids



if __name__ == "__main__":
    # Here's an opportunity to test offline against some TA agents. Just run this file to do so.
    test_agents = [MyNDaysNCampaignsAgent()] + [Tier1NDaysNCampaignsAgent(name=f"Agent {i + 1}") for i in range(9)]

    # Don't change this. Adapt initialization to your environment
    simulator = AdXGameSimulator()
    simulator.run_simulation(agents=test_agents, num_simulations=500)
    #simulator.run_simulation(agents=test_agents, num_simulations=300)