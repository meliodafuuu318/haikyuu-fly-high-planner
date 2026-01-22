import random
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
from banners import BANNERS

class GachaSimulator:
    def __init__(self):
        # Constants
        self.PULL_COST = 150
        
        # UR rates
        self.UR_BASE_RATE = 0.001  # 0.1%
        self.UR_SOFT_PITY_START = 80
        self.UR_PITY_START = 81
        self.UR_PITY_INCREMENT = 0.0022  # 0.22%
        self.UR_HARD_PITY = 140
        
        # SP rates
        self.SP_BASE_RATE = 0.001  # 0.1%
        self.SP_SOFT_PITY_START = 90
        self.SP_PITY_START = 91
        self.SP_PITY_INCREMENT = 0.0032  # 0.32%
        self.SP_HARD_PITY = 140
        
        # Hardcoded banner schedule (name, type, start_date, end_date)
        self.BANNERS = BANNERS
    
    def calculate_ur_rate(self, pity_count):
        """Calculate UR drop rate based on current pity count"""
        if pity_count < self.UR_PITY_START:
            return self.UR_BASE_RATE
        
        pulls_into_pity = pity_count - self.UR_PITY_START + 1
        rate = self.UR_BASE_RATE + (pulls_into_pity * self.UR_PITY_INCREMENT)
        return min(rate, 0.1308)  # Cap at 13.08%
    
    def calculate_sp_rate(self, pity_count):
        """Calculate SP drop rate based on current pity count"""
        if pity_count < self.SP_PITY_START:
            return self.SP_BASE_RATE
        
        pulls_into_pity = pity_count - self.SP_PITY_START + 1
        rate = self.SP_BASE_RATE + (pulls_into_pity * self.SP_PITY_INCREMENT)
        return min(rate, 0.1578)  # Cap at 15.78%
    
    def simulate_single_pull(self, pity_count, banner_type):
        """Simulate a single pull and return if featured obtained and new pity"""
        if banner_type == "UR":
            if pity_count >= self.UR_HARD_PITY - 1:
                return True, 0
            rate = self.calculate_ur_rate(pity_count)
        else:  # SP
            if pity_count >= self.SP_HARD_PITY - 1:
                return True, 0
            rate = self.calculate_sp_rate(pity_count)
        
        got_featured = random.random() < rate
        
        if got_featured:
            return True, 0
        else:
            return False, pity_count + 1
    
    def simulate_banner(self, diamonds, tickets, pity, target_copies, banner_type):
        """Simulate pulling on a single banner until target copies obtained"""
        total_pulls = 0
        pulls_with_diamonds = 0
        pulls_on_this_banner = 0
        copies_obtained = 0
        tickets_used = 0
        milestone_tickets = 0
        milestone_copies = 0
        
        current_pity = pity
        current_diamonds = diamonds
        current_tickets = tickets
        
        while copies_obtained < target_copies:
            # Check if we have any resources left
            can_pull_with_ticket = current_tickets > 0
            can_pull_with_diamonds = current_diamonds >= self.PULL_COST
            
            if not can_pull_with_ticket and not can_pull_with_diamonds:
                # No resources left
                break
            
            # Use tickets first, then diamonds
            if can_pull_with_ticket:
                current_tickets -= 1
                tickets_used += 1
            elif can_pull_with_diamonds:
                current_diamonds -= self.PULL_COST
                pulls_with_diamonds += 1
            
            total_pulls += 1
            pulls_on_this_banner += 1
            
            # Simulate pull
            got_featured, current_pity = self.simulate_single_pull(current_pity, banner_type)
            
            if got_featured:
                copies_obtained += 1
            
            # Check milestone rewards (no carryover, only for this banner)
            if pulls_on_this_banner == 10:
                milestone_tickets += 2
                current_tickets += 2
            elif pulls_on_this_banner == 50:
                milestone_tickets += 5
                current_tickets += 5
            elif pulls_on_this_banner == 200:
                milestone_copies += 1
                copies_obtained += 1
        
        return {
            'success': copies_obtained >= target_copies,
            'total_pulls': total_pulls,
            'pulls_with_diamonds': pulls_with_diamonds,
            'tickets_used': tickets_used,
            'milestone_tickets': milestone_tickets,
            'milestone_copies': milestone_copies,
            'copies_obtained': copies_obtained,
            'diamonds_remaining': current_diamonds,
            'tickets_remaining': current_tickets,
            'final_pity': current_pity,
            'diamonds_spent': pulls_with_diamonds * self.PULL_COST
        }
    
    def get_banner_tag(self, banner_name):
        """Determine if banner is a rebanner or new release"""
        if "Rebanner" in banner_name:
            return "rebanner"
        else:
            return "new release"
    
    def run_monte_carlo(self, initial_diamonds, initial_ur_tickets, initial_sp_tickets,
                       initial_ur_pity, initial_sp_pity, free_ur_tickets, free_sp_tickets,
                       targeted_banners, daily_income, num_simulations=10000):
        """Run Monte Carlo simulation"""
        
        # Sort targeted banners by date
        sorted_targets = []
        for banner_name, target_copies in targeted_banners:
            banner_info = None
            for b in self.BANNERS:
                if b[0] == banner_name:
                    banner_info = b
                    break
            if banner_info:
                sorted_targets.append((banner_name, target_copies, banner_info[2]))  # Add start_date
        
        # Sort by start date
        sorted_targets.sort(key=lambda x: x[2])
        # Remove the date from the tuple
        targeted_banners = [(name, copies) for name, copies, _ in sorted_targets]
        
        # Create set of targeted banner names for quick lookup
        targeted_banner_names = {name for name, _ in targeted_banners}
        
        results = []
        
        for sim in range(num_simulations):
            diamonds = initial_diamonds
            ur_tickets = initial_ur_tickets
            sp_tickets = initial_sp_tickets
            ur_pity = initial_ur_pity
            sp_pity = initial_sp_pity
            
            current_date = datetime.now()
            sim_success = True
            banner_results = []
            last_banner_end_date = current_date
            
            for banner_name, target_copies in targeted_banners:
                # Find banner info
                banner_info = None
                for b in self.BANNERS:
                    if b[0] == banner_name:
                        banner_info = b
                        break
                
                if not banner_info:
                    continue
                
                _, banner_type, start_date, end_date = banner_info
                
                # Skip banners that have already ended
                if end_date < current_date:
                    continue
                
                # Get banner tag (rebanner or new release)
                banner_tag = self.get_banner_tag(banner_name)
                
                # Track diamonds at start of this banner (before adding income)
                diamonds_before_income = diamonds
                
                # Calculate free tickets from all banners (selected or not) between last banner and this one
                free_ur_gained = 0
                free_sp_gained = 0
                
                for b in self.BANNERS:
                    b_name, b_type, b_start, b_end = b
                    # Check if banner falls between last targeted banner and current targeted banner
                    if b_start >= last_banner_end_date and b_end <= start_date:
                        b_tag = self.get_banner_tag(b_name)
                        if b_tag == "new release":
                            if b_type == "UR":
                                free_ur_gained += free_ur_tickets
                            else:  # SP
                                free_sp_gained += free_sp_tickets
                
                # Add free tickets from current banner if it's a new release
                if banner_tag == "new release":
                    if banner_type == "UR":
                        free_ur_gained += free_ur_tickets
                    else:
                        free_sp_gained += free_sp_tickets
                
                # Add the free tickets to inventory
                ur_tickets += free_ur_gained
                sp_tickets += free_sp_gained
                
                # Calculate days until banner starts and add daily income
                if start_date > current_date:
                    days_diff = (start_date - current_date).days
                    diamonds += days_diff * daily_income
                    current_date = start_date
                
                # Calculate actual days remaining in banner based on current date
                # If banner already started, use current_date; otherwise use start_date
                effective_start = max(current_date, start_date)
                
                # Calculate days remaining, ensuring at least 1 day if banner is still active
                banner_duration_days = max(1, (end_date - effective_start).days)
                
                # Add diamonds earned during the remaining banner duration
                diamonds += banner_duration_days * daily_income
                
                # Calculate total diamonds gained since last banner
                total_diamonds_gained = diamonds - diamonds_before_income
                
                # Determine which tickets and pity to use
                if banner_type == "UR":
                    tickets = ur_tickets
                    pity = ur_pity
                else:
                    tickets = sp_tickets
                    pity = sp_pity
                
                # Simulate banner - now properly uses ALL available resources
                result = self.simulate_banner(
                    diamonds, tickets, pity, target_copies, banner_type
                )
                
                # Update resources
                diamonds = result['diamonds_remaining']
                
                # Update tickets and pity based on banner type
                if banner_type == "UR":
                    ur_tickets = result['tickets_remaining']
                    ur_pity = result['final_pity']
                else:
                    sp_tickets = result['tickets_remaining']
                    sp_pity = result['final_pity']
                
                result['banner_name'] = banner_name
                result['banner_type'] = banner_type
                result['banner_tag'] = banner_tag
                result['banner_start_date'] = start_date
                result['banner_end_date'] = end_date
                result['banner_duration_days'] = banner_duration_days
                result['total_diamonds_gained'] = total_diamonds_gained
                result['free_ur_tickets_gained'] = free_ur_gained
                result['free_sp_tickets_gained'] = free_sp_gained
                result['milestone_tickets_gained'] = result['milestone_tickets']
                result['remaining_diamonds'] = diamonds
                result['remaining_ur_tickets'] = ur_tickets
                result['remaining_sp_tickets'] = sp_tickets
                result['remaining_ur_pity'] = ur_pity
                result['remaining_sp_pity'] = sp_pity
                banner_results.append(result)
                
                if not result['success']:
                    sim_success = False
                
                # Move current date to end of banner and update last banner end date
                current_date = end_date
                last_banner_end_date = end_date
            
            results.append({
                'success': sim_success,
                'banner_results': banner_results,
                'final_diamonds': diamonds,
                'final_ur_tickets': ur_tickets,
                'final_sp_tickets': sp_tickets
            })
        
        return self.analyze_results(results, num_simulations, targeted_banners)
    
    def analyze_results(self, results, num_sims, targeted_banners):
        """Analyze simulation results"""
        success_count = sum(1 for r in results if r['success'])
        success_rate = (success_count / num_sims) * 100
        
        # Per-banner statistics
        banner_stats = defaultdict(lambda: {
            'total_pulls': [],
            'diamonds_spent': [],
            'tickets_used': [],
            'success_count': 0,
            'remaining_diamonds': [],
            'remaining_ur_tickets': [],
            'remaining_sp_tickets': [],
            'start_date': None,
            'end_date': None,
            'duration_days': 0,
            'total_diamonds_gained': [],
            'free_ur_tickets_gained': [],
            'free_sp_tickets_gained': [],
            'milestone_tickets_gained': [],
            'milestone_copies': [],
            'banner_tag': None
        })
        
        for result in results:
            for banner_result in result['banner_results']:
                name = banner_result['banner_name']
                banner_stats[name]['total_pulls'].append(banner_result['total_pulls'])
                banner_stats[name]['diamonds_spent'].append(banner_result['diamonds_spent'])
                banner_stats[name]['tickets_used'].append(banner_result['tickets_used'])
                banner_stats[name]['remaining_diamonds'].append(banner_result['remaining_diamonds'])
                banner_stats[name]['remaining_ur_tickets'].append(banner_result['remaining_ur_tickets'])
                banner_stats[name]['remaining_sp_tickets'].append(banner_result['remaining_sp_tickets'])
                banner_stats[name]['total_diamonds_gained'].append(banner_result['total_diamonds_gained'])
                banner_stats[name]['free_ur_tickets_gained'].append(banner_result['free_ur_tickets_gained'])
                banner_stats[name]['free_sp_tickets_gained'].append(banner_result['free_sp_tickets_gained'])
                banner_stats[name]['milestone_tickets_gained'].append(banner_result['milestone_tickets_gained'])
                banner_stats[name]['milestone_copies'].append(banner_result['milestone_copies'])
                base_copies = banner_result['copies_obtained'] - banner_result['milestone_copies']
                banner_stats[name].setdefault('base_copies', []).append(base_copies)
                banner_stats[name]['start_date'] = banner_result['banner_start_date']
                banner_stats[name]['end_date'] = banner_result['banner_end_date']
                banner_stats[name]['duration_days'] = banner_result['banner_duration_days']
                banner_stats[name]['banner_tag'] = banner_result['banner_tag']
                if banner_result['success']:
                    banner_stats[name]['success_count'] += 1
        
        # Calculate percentiles
        analysis = {
            'success_rate': success_rate,
            'total_simulations': num_sims,
            'banner_statistics': {}
        }
        
        for banner_name, _ in targeted_banners:
            if banner_name in banner_stats:
                stats = banner_stats[banner_name]
                analysis['banner_statistics'][banner_name] = {
                    'avg_pulls': np.mean(stats['total_pulls']),
                    'median_pulls': np.median(stats['total_pulls']),
                    'p10_pulls': np.percentile(stats['total_pulls'], 10),
                    'p50_pulls': np.percentile(stats['total_pulls'], 50),
                    'p90_pulls': np.percentile(stats['total_pulls'], 90),
                    'avg_diamonds': np.mean(stats['diamonds_spent']),
                    'median_diamonds': np.median(stats['diamonds_spent']),
                    'p10_diamonds': np.percentile(stats['diamonds_spent'], 10),
                    'p50_diamonds': np.percentile(stats['diamonds_spent'], 50),
                    'p90_diamonds': np.percentile(stats['diamonds_spent'], 90),
                    'success_rate': (stats['success_count'] / num_sims) * 100,
                    'avg_remaining_diamonds': np.mean(stats['remaining_diamonds']),
                    'median_remaining_diamonds': np.median(stats['remaining_diamonds']),
                    'avg_remaining_ur_tickets': np.mean(stats['remaining_ur_tickets']),
                    'median_remaining_ur_tickets': np.median(stats['remaining_ur_tickets']),
                    'avg_remaining_sp_tickets': np.mean(stats['remaining_sp_tickets']),
                    'median_remaining_sp_tickets': np.median(stats['remaining_sp_tickets']),
                    'total_diamonds_gained': int(np.mean(stats['total_diamonds_gained'])),
                    'free_ur_tickets_gained': int(np.mean(stats['free_ur_tickets_gained'])),
                    'free_sp_tickets_gained': int(np.mean(stats['free_sp_tickets_gained'])),
                    'milestone_tickets_gained': float(np.mean(stats['milestone_tickets_gained'])),
                    'milestone_copies_rate': float(np.mean(stats['milestone_copies'])),
                    'avg_base_copies': float(np.mean(stats['base_copies'])) if 'base_copies' in stats else 0,
                    'start_date': stats['start_date'],
                    'end_date': stats['end_date'],
                    'duration_days': stats['duration_days'],
                    'banner_tag': stats['banner_tag']
                }
        
        return analysis


def main():
    print("=" * 70)
    print("Haikyuu Fly High Gacha Monte Carlo Simulation")
    print("=" * 70)
    
    sim = GachaSimulator()
    
    # Display available banners
    print("\nAvailable Banners:")
    for i, (name, b_type, start, end) in enumerate(sim.BANNERS, 1):
        print(f"{i}. {name} ({b_type}) - {start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}")
    
    # User inputs
    print("\n" + "=" * 70)
    print("Enter your current resources:")
    print("=" * 70)
    
    diamonds = int(input("On-hand diamonds: "))
    ur_tickets = int(input("On-hand UR tickets: "))
    sp_tickets = int(input("On-hand SP tickets: "))
    ur_pity = int(input("Current UR pity count (0-139): "))
    sp_pity = int(input("Current SP pity count (0-139): "))
    free_ur = int(input("Free UR tickets per UR banner: "))
    free_sp = int(input("Free SP tickets per SP banner: "))
    daily_income = int(input("Daily diamond income: "))
    
    # Targeted banners
    print("\n" + "=" * 70)
    print("Enter targeted banners:")
    print("=" * 70)
    
    num_targets = int(input("How many banners do you want to target? "))
    targeted_banners = []
    
    for i in range(num_targets):
        print(f"\nTarget {i+1}:")
        banner_num = int(input(f"  Banner number (1-{len(sim.BANNERS)}): "))
        copies = int(input("  Target copies: "))
        targeted_banners.append((sim.BANNERS[banner_num - 1][0], copies))
    
    num_sims = int(input("\nNumber of simulations (default 10000): ") or "10000")
    
    # Run simulation
    print("\n" + "=" * 70)
    print("Running simulation...")
    print("=" * 70)
    
    analysis = sim.run_monte_carlo(
        diamonds, ur_tickets, sp_tickets, ur_pity, sp_pity,
        free_ur, free_sp, targeted_banners, daily_income, num_sims
    )
    
    # Display results
    print("\n" + "=" * 70)
    print("SIMULATION RESULTS")
    print("=" * 70)
    print(f"\nOverall Success Rate: {analysis['success_rate']:.2f}%")
    print(f"Total Simulations: {analysis['total_simulations']}")
    
    print("\n" + "=" * 70)
    print("PER-BANNER STATISTICS (in chronological order)")
    print("=" * 70)
    
    # Sort banners by start date for display
    sorted_banner_names = sorted(
        analysis['banner_statistics'].keys(),
        key=lambda x: analysis['banner_statistics'][x]['start_date']
    )
    
    for banner_name in sorted_banner_names:
        stats = analysis['banner_statistics'][banner_name]
        tag_display = f"[{stats['banner_tag'].upper()}]"
        print(f"\n{banner_name} {tag_display}")
        print(f"  Period: {stats['start_date'].strftime('%Y-%m-%d')} to {stats['end_date'].strftime('%Y-%m-%d')} ({stats['duration_days']} days)")
        print(f"\n  RESOURCES GAINED SINCE LAST BANNER:")
        print(f"    Total Diamonds: {stats['total_diamonds_gained']:,}")
        print(f"    Free UR Tickets: {stats['free_ur_tickets_gained']}")
        print(f"    Free SP Tickets: {stats['free_sp_tickets_gained']}")
        print(f"\n  MILESTONE REWARDS (THIS BANNER):")
        print(f"    Milestone Tickets (Avg): {stats['milestone_tickets_gained']:.1f}")
        print(
            f"    Extra Copy @ 200 Pulls: "
            f"{stats['milestone_copies_rate'] * 100:.1f}%"
        )
        print(f"\n  Success Rate: {stats['success_rate']:.2f}%")
        print(f"  Average Pulls: {stats['avg_pulls']:.1f}")
        print(f"  Median Pulls: {stats['median_pulls']:.1f}")
        print(f"  Average Base Copies Obtained: {stats['avg_base_copies']:.2f}")
        print(f"  10th Percentile: {stats['p10_pulls']:.1f} pulls")
        print(f"  50th Percentile: {stats['p50_pulls']:.1f} pulls")
        print(f"  90th Percentile: {stats['p90_pulls']:.1f} pulls")
        print(f"  Average Diamonds Spent: {stats['avg_diamonds']:.0f}")
        print(f"  Median Diamonds Spent: {stats['median_diamonds']:.0f}")
        print(f"  10th Percentile: {stats['p10_diamonds']:.0f} diamonds")
        print(f"  50th Percentile: {stats['p50_diamonds']:.0f} diamonds")
        print(f"  90th Percentile: {stats['p90_diamonds']:.0f} diamonds")
        print(f"\n  REMAINING RESOURCES AFTER THIS BANNER:")
        print(f"    Avg Diamonds: {stats['avg_remaining_diamonds']:.0f} | Median: {stats['median_remaining_diamonds']:.0f}")
        print(f"    Avg UR Tickets: {stats['avg_remaining_ur_tickets']:.1f} | Median: {stats['median_remaining_ur_tickets']:.1f}")
        print(f"    Avg SP Tickets: {stats['avg_remaining_sp_tickets']:.1f} | Median: {stats['median_remaining_sp_tickets']:.1f}")


if __name__ == "__main__":
    main()