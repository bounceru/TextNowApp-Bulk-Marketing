"""
Enhanced Campaign Schedule for TextNow Max

This module provides enhanced campaign scheduling functionality for the TextNow Max application,
supporting large volume messaging with configurable timing, patterns, and intelligent distribution.
"""

def generate_campaign_schedule_html():
    """Generate the enhanced campaign scheduling interface HTML"""
    return '''
    <div class="app-container">
        <div class="app-content">
            <div class="content-card" style="margin-bottom: 25px;">
                <div class="card-header">
                    <div style="font-size: 20px; font-weight: bold; color: #EEE;">Active Campaign Schedule</div>
                </div>
                <div class="card-body">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                        <div style="flex: 1;">
                            <div style="font-weight: bold; margin-bottom: 5px;">Florida Mass Campaign</div>
                            <div style="font-size: 13px; color: #888;">Currently distributing 100,000 messages across 8am-8pm window</div>
                        </div>
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <div style="background-color: #dff0d8; border-radius: 4px; padding: 3px 8px; font-size: 12px; color: #3c763d;">Active</div>
                            <button class="form-button secondary-button">Pause</button>
                            <button class="form-button secondary-button">Edit</button>
                        </div>
                    </div>
                    
                    <div style="height: 6px; background-color: #3A3A3A; border-radius: 3px; margin-bottom: 10px; overflow: hidden;">
                        <div style="height: 100%; width: 37%; background-color: #5cb85c; border-radius: 3px;"></div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 12px; color: #888; margin-bottom: 20px;">
                        <div>0 messages</div>
                        <div>37,214 / 100,000 messages sent</div>
                        <div>100,000 messages</div>
                    </div>
                    
                    <div style="display: flex; gap: 20px; margin-bottom: 30px;">
                        <div style="flex: 1; background-color: #252525; border-radius: 8px; padding: 15px;">
                            <div style="font-weight: bold; margin-bottom: 10px; color: #EEE;">Distribution Parameters</div>
                            <div style="display: grid; grid-template-columns: auto 1fr; row-gap: 8px; column-gap: 15px; font-size: 13px;">
                                <div style="color: #AAA;">Time Window:</div>
                                <div style="color: #EEE;">8:00 AM - 8:00 PM</div>
                                <div style="color: #AAA;">Distribution Pattern:</div>
                                <div style="color: #EEE;">Natural Bell Curve</div>
                                <div style="color: #AAA;">Target Rate:</div>
                                <div style="color: #EEE;">~8,333 messages per hour</div>
                                <div style="color: #AAA;">Account Rotation:</div>
                                <div style="color: #EEE;">Random w/ Health Prioritization</div>
                                <div style="color: #AAA;">Area Code Focus:</div>
                                <div style="color: #EEE;">Florida (954, 754, 305, 786, 561)</div>
                            </div>
                        </div>
                        
                        <div style="flex: 1; background-color: #252525; border-radius: 8px; padding: 15px;">
                            <div style="font-weight: bold; margin-bottom: 10px; color: #EEE;">Performance Metrics</div>
                            <div style="display: grid; grid-template-columns: auto 1fr; row-gap: 8px; column-gap: 15px; font-size: 13px;">
                                <div style="color: #AAA;">Accounts In Use:</div>
                                <div style="color: #EEE;">427 / 5,721 available</div>
                                <div style="color: #AAA;">Current Send Rate:</div>
                                <div style="color: #EEE;">9,271 messages / hour</div>
                                <div style="color: #AAA;">Delivery Success:</div>
                                <div style="color: #EEE;">98.7%</div>
                                <div style="color: #AAA;">Response Rate:</div>
                                <div style="color: #EEE;">4.2% (1,564 responses)</div>
                                <div style="color: #AAA;">Estimated Completion:</div>
                                <div style="color: #EEE;">Today at 5:42 PM</div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="font-weight: bold; margin-bottom: 10px; color: #EEE;">Hourly Distribution</div>
                    <div style="display: flex; height: 100px; align-items: flex-end; margin-bottom: 5px;">
                        <div style="flex: 1; height: 35%; background-color: #5cb85c; margin-right: 2px; position: relative;">
                            <div style="position: absolute; top: -20px; width: 100%; text-align: center; font-size: 11px; color: #AAA;">8am</div>
                        </div>
                        <div style="flex: 1; height: 55%; background-color: #5cb85c; margin-right: 2px; position: relative;">
                            <div style="position: absolute; top: -20px; width: 100%; text-align: center; font-size: 11px; color: #AAA;">9am</div>
                        </div>
                        <div style="flex: 1; height: 78%; background-color: #5cb85c; margin-right: 2px; position: relative;">
                            <div style="position: absolute; top: -20px; width: 100%; text-align: center; font-size: 11px; color: #AAA;">10am</div>
                        </div>
                        <div style="flex: 1; height: 92%; background-color: #5cb85c; margin-right: 2px; position: relative;">
                            <div style="position: absolute; top: -20px; width: 100%; text-align: center; font-size: 11px; color: #AAA;">11am</div>
                        </div>
                        <div style="flex: 1; height: 98%; background-color: #5cb85c; margin-right: 2px; position: relative;">
                            <div style="position: absolute; top: -20px; width: 100%; text-align: center; font-size: 11px; color: #AAA;">12pm</div>
                        </div>
                        <div style="flex: 1; height: 90%; background-color: #444; margin-right: 2px; position: relative;">
                            <div style="position: absolute; top: -20px; width: 100%; text-align: center; font-size: 11px; color: #AAA;">1pm</div>
                        </div>
                        <div style="flex: 1; height: 80%; background-color: #444; margin-right: 2px; position: relative;">
                            <div style="position: absolute; top: -20px; width: 100%; text-align: center; font-size: 11px; color: #AAA;">2pm</div>
                        </div>
                        <div style="flex: 1; height: 70%; background-color: #444; margin-right: 2px; position: relative;">
                            <div style="position: absolute; top: -20px; width: 100%; text-align: center; font-size: 11px; color: #AAA;">3pm</div>
                        </div>
                        <div style="flex: 1; height: 58%; background-color: #444; margin-right: 2px; position: relative;">
                            <div style="position: absolute; top: -20px; width: 100%; text-align: center; font-size: 11px; color: #AAA;">4pm</div>
                        </div>
                        <div style="flex: 1; height: 49%; background-color: #444; margin-right: 2px; position: relative;">
                            <div style="position: absolute; top: -20px; width: 100%; text-align: center; font-size: 11px; color: #AAA;">5pm</div>
                        </div>
                        <div style="flex: 1; height: 40%; background-color: #444; margin-right: 2px; position: relative;">
                            <div style="position: absolute; top: -20px; width: 100%; text-align: center; font-size: 11px; color: #AAA;">6pm</div>
                        </div>
                        <div style="flex: 1; height: 30%; background-color: #444; position: relative;">
                            <div style="position: absolute; top: -20px; width: 100%; text-align: center; font-size: 11px; color: #AAA;">7pm</div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                        <div style="font-size: 12px; color: #888;">Hours in green: completed</div>
                        <div style="font-size: 12px; color: #888;">Peak: 12:00pm (~10,800 messages)</div>
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <button class="form-button">Export Campaign Stats</button>
                    </div>
                </div>
            </div>
            
            <div class="content-card" style="margin-bottom: 25px;">
                <div class="card-header">
                    <div style="font-size: 20px; font-weight: bold; color: #EEE;">Create New Campaign Schedule</div>
                </div>
                <div class="card-body">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                        <div>
                            <label class="form-label">Campaign Name</label>
                            <input type="text" class="form-input" placeholder="Enter campaign name">
                        </div>
                        <div>
                            <label class="form-label">Associated Campaign</label>
                            <select class="form-select">
                                <option>Select a campaign</option>
                                <option>Florida Spring Promotion</option>
                                <option>Text-to-Win Contest</option>
                                <option>April Discount Code</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="form-label">Total Messages to Send</label>
                            <input type="number" class="form-input" placeholder="Number of messages" value="100000">
                        </div>
                        <div>
                            <label class="form-label">Target Area Codes</label>
                            <input type="text" class="form-input" placeholder="Comma-separated area codes" value="954, 754, 305, 786, 561">
                        </div>
                        
                        <div>
                            <label class="form-label">Distribution Start Time</label>
                            <input type="time" class="form-input" value="08:00">
                        </div>
                        <div>
                            <label class="form-label">Distribution End Time</label>
                            <input type="time" class="form-input" value="20:00">
                        </div>
                        
                        <div>
                            <label class="form-label">Distribution Pattern</label>
                            <select class="form-select">
                                <option selected>Natural Bell Curve (Recommended)</option>
                                <option>Even Distribution</option>
                                <option>Morning Heavy</option>
                                <option>Afternoon Heavy</option>
                                <option>Custom Pattern</option>
                            </select>
                        </div>
                        <div>
                            <label class="form-label">Account Selection</label>
                            <select class="form-select">
                                <option selected>Optimized Auto-Selection</option>
                                <option>Newest Accounts Only</option>
                                <option>Oldest Accounts Only</option>
                                <option>High Health Score Priority</option>
                                <option>Custom Filter...</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="form-label">Message Template Variation</label>
                            <select class="form-select">
                                <option selected>Balanced Random</option>
                                <option>Strict A/B Testing</option>
                                <option>Weighted by Performance</option>
                                <option>Single Template</option>
                            </select>
                        </div>
                        <div>
                            <label class="form-label">Image Variation</label>
                            <select class="form-select">
                                <option selected>Random from Campaign Set</option>
                                <option>No Images</option>
                                <option>Single Image</option>
                                <option>Sequential Rotation</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="form-label">Maximum Messages per Account</label>
                            <input type="number" class="form-input" value="250">
                        </div>
                        <div>
                            <label class="form-label">Delivery Speed Priority</label>
                            <select class="form-select">
                                <option>Maximum Speed</option>
                                <option selected>Balanced (Recommended)</option>
                                <option>Safety First</option>
                                <option>Custom Rate Limit...</option>
                            </select>
                        </div>
                        
                        <div>
                            <label class="form-label">Start Date</label>
                            <input type="date" class="form-input" value="2025-04-25">
                        </div>
                        <div>
                            <label class="form-label">Response Handling</label>
                            <select class="form-select">
                                <option selected>Auto-Response (Template Based)</option>
                                <option>Log Only (No Response)</option>
                                <option>Forward to Manual Queue</option>
                                <option>Chatbot Response</option>
                            </select>
                        </div>
                        
                        <div style="grid-column: span 2;">
                            <label class="form-label">Advanced Options</label>
                            <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                                <div style="display: flex; align-items: center;">
                                    <input type="checkbox" id="account_health" checked style="margin-right: 8px;">
                                    <label for="account_health" style="color: #EEE;">Enable account health monitoring</label>
                                </div>
                                <div style="display: flex; align-items: center;">
                                    <input type="checkbox" id="dynamic_adjust" checked style="margin-right: 8px;">
                                    <label for="dynamic_adjust" style="color: #EEE;">Dynamically adjust for response rates</label>
                                </div>
                                <div style="display: flex; align-items: center;">
                                    <input type="checkbox" id="rate_limiting" checked style="margin-right: 8px;">
                                    <label for="rate_limiting" style="color: #EEE;">Apply intelligent rate limiting</label>
                                </div>
                                <div style="display: flex; align-items: center;">
                                    <input type="checkbox" id="error_correction" checked style="margin-right: 8px;">
                                    <label for="error_correction" style="color: #EEE;">Automatic error correction</label>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="text-align: right; margin-top: 20px;">
                        <button class="form-button secondary-button" style="margin-right: 10px;">Save as Draft</button>
                        <button class="form-button">Schedule Campaign</button>
                    </div>
                </div>
            </div>
            
            <div class="content-card">
                <div class="card-header">
                    <div style="font-size: 20px; font-weight: bold; color: #EEE;">Saved Campaign Schedules</div>
                </div>
                <div class="card-body">
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; color: #EEE;">
                        <thead>
                            <tr style="background-color: #2A2A2A; border-bottom: 1px solid #444;">
                                <th style="padding: 10px; text-align: left;">Name</th>
                                <th style="padding: 10px; text-align: left;">Status</th>
                                <th style="padding: 10px; text-align: left;">Progress</th>
                                <th style="padding: 10px; text-align: left;">Total Messages</th>
                                <th style="padding: 10px; text-align: left;">Timeframe</th>
                                <th style="padding: 10px; text-align: left;">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid #444;">
                                <td style="padding: 10px;">Florida Mass Campaign</td>
                                <td style="padding: 10px;">
                                    <span style="background-color: #1e3e1e; border-radius: 4px; padding: 3px 8px; font-size: 12px; color: #4CAF50;">Active</span>
                                </td>
                                <td style="padding: 10px;">37%</td>
                                <td style="padding: 10px;">100,000</td>
                                <td style="padding: 10px;">Apr 25, 8am-8pm</td>
                                <td style="padding: 10px;">
                                    <button class="form-button secondary-button" style="padding: 3px 8px; font-size: 12px; margin-right: 5px;">View</button>
                                    <button class="form-button secondary-button" style="padding: 3px 8px; font-size: 12px;">Pause</button>
                                </td>
                            </tr>
                            <tr style="border-bottom: 1px solid #444;">
                                <td style="padding: 10px;">Text-to-Win Contest</td>
                                <td style="padding: 10px;">
                                    <span style="background-color: #3a3022; border-radius: 4px; padding: 3px 8px; font-size: 12px; color: #FFC107;">Scheduled</span>
                                </td>
                                <td style="padding: 10px;">0%</td>
                                <td style="padding: 10px;">50,000</td>
                                <td style="padding: 10px;">Apr 27, 9am-7pm</td>
                                <td style="padding: 10px;">
                                    <button class="form-button secondary-button" style="padding: 3px 8px; font-size: 12px; margin-right: 5px;">Edit</button>
                                    <button class="form-button secondary-button" style="padding: 3px 8px; font-size: 12px;">Cancel</button>
                                </td>
                            </tr>
                            <tr style="border-bottom: 1px solid #444;">
                                <td style="padding: 10px;">Spring Promo Phase 1</td>
                                <td style="padding: 10px;">
                                    <span style="background-color: #142c3a; border-radius: 4px; padding: 3px 8px; font-size: 12px; color: #03A9F4;">Draft</span>
                                </td>
                                <td style="padding: 10px;">-</td>
                                <td style="padding: 10px;">75,000</td>
                                <td style="padding: 10px;">-</td>
                                <td style="padding: 10px;">
                                    <button class="form-button secondary-button" style="padding: 3px 8px; font-size: 12px; margin-right: 5px;">Edit</button>
                                    <button class="form-button secondary-button" style="padding: 3px 8px; font-size: 12px;">Delete</button>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 10px;">Weekly Check-in</td>
                                <td style="padding: 10px;">
                                    <span style="background-color: #3e1e1e; border-radius: 4px; padding: 3px 8px; font-size: 12px; color: #F44336;">Completed</span>
                                </td>
                                <td style="padding: 10px;">100%</td>
                                <td style="padding: 10px;">25,000</td>
                                <td style="padding: 10px;">Apr 20, 8am-6pm</td>
                                <td style="padding: 10px;">
                                    <button class="form-button secondary-button" style="padding: 3px 8px; font-size: 12px; margin-right: 5px;">View</button>
                                    <button class="form-button secondary-button" style="padding: 3px 8px; font-size: 12px;">Clone</button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <div style="text-align: right; margin-top: 20px;">
                        <button class="form-button secondary-button" style="margin-right: 10px;">View All Campaigns</button>
                        <button class="form-button">Create New Schedule</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    '''