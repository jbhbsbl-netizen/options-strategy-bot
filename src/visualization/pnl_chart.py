"""
P/L Chart Visualization

Creates interactive Plotly charts for options strategy P/L visualization.
"""
import plotly.graph_objects as go
import pandas as pd
from typing import List, Optional


def create_pnl_chart(
    pnl_curve: pd.DataFrame,
    current_price: float,
    max_profit: float,
    max_loss: float,
    max_profit_price: float,
    max_loss_price: float,
    breakevens: List[float],
    strategy_name: str = "Options Strategy",
    target_price: Optional[float] = None
) -> go.Figure:
    """
    Create interactive P/L chart with Plotly.

    Args:
        pnl_curve: DataFrame with columns 'stock_price' and 'pnl'
        current_price: Current stock price
        max_profit: Maximum profit value
        max_loss: Maximum loss value
        max_profit_price: Stock price at max profit
        max_loss_price: Stock price at max loss
        breakevens: List of breakeven prices
        strategy_name: Name of strategy for title
        target_price: Optional target price to mark on chart

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    # Split P/L curve into profit and loss zones for coloring
    df = pnl_curve.copy()
    df['profit_zone'] = df['pnl'] >= 0

    # Add P/L line
    fig.add_trace(go.Scatter(
        x=df['stock_price'],
        y=df['pnl'],
        mode='lines',
        name='P/L at Expiration',
        line=dict(color='#1f77b4', width=3),
        hovertemplate='<b>Price: $%{x:.2f}</b><br>P/L: $%{y:,.2f}<extra></extra>'
    ))

    # Add profit zone (green fill above zero)
    profit_mask = df['pnl'] >= 0
    if profit_mask.any():
        fig.add_trace(go.Scatter(
            x=df[profit_mask]['stock_price'],
            y=df[profit_mask]['pnl'],
            fill='tonexty',
            fillcolor='rgba(0, 255, 0, 0.1)',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))

    # Add loss zone (red fill below zero)
    loss_mask = df['pnl'] < 0
    if loss_mask.any():
        fig.add_trace(go.Scatter(
            x=df[loss_mask]['stock_price'],
            y=df[loss_mask]['pnl'],
            fill='tozeroy',
            fillcolor='rgba(255, 0, 0, 0.1)',
            line=dict(width=0),
            showlegend=False,
            hoverinfo='skip'
        ))

    # Add zero line
    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="gray",
        annotation_text="Breakeven",
        annotation_position="right"
    )

    # Add current price line
    fig.add_vline(
        x=current_price,
        line_dash="dash",
        line_color="blue",
        annotation_text=f"Current: ${current_price:.2f}",
        annotation_position="top"
    )

    # Add target price line if provided
    if target_price:
        fig.add_vline(
            x=target_price,
            line_dash="dot",
            line_color="purple",
            annotation_text=f"Target: ${target_price:.2f}",
            annotation_position="top"
        )

    # Add max profit marker
    fig.add_trace(go.Scatter(
        x=[max_profit_price],
        y=[max_profit],
        mode='markers+text',
        name='Max Profit',
        marker=dict(color='green', size=12, symbol='star'),
        text=[f"Max Profit<br>${max_profit:,.2f}"],
        textposition='top center',
        textfont=dict(color='green', size=10),
        hovertemplate=f'<b>Max Profit: ${max_profit:,.2f}</b><br>At price: ${max_profit_price:.2f}<extra></extra>'
    ))

    # Add max loss marker
    fig.add_trace(go.Scatter(
        x=[max_loss_price],
        y=[max_loss],
        mode='markers+text',
        name='Max Loss',
        marker=dict(color='red', size=12, symbol='x'),
        text=[f"Max Loss<br>${max_loss:,.2f}"],
        textposition='bottom center',
        textfont=dict(color='red', size=10),
        hovertemplate=f'<b>Max Loss: ${max_loss:,.2f}</b><br>At price: ${max_loss_price:.2f}<extra></extra>'
    ))

    # Add breakeven markers
    for i, be in enumerate(breakevens):
        fig.add_trace(go.Scatter(
            x=[be],
            y=[0],
            mode='markers+text',
            name=f'Breakeven {i+1}' if len(breakevens) > 1 else 'Breakeven',
            marker=dict(color='orange', size=10, symbol='diamond'),
            text=[f"BE: ${be:.2f}"],
            textposition='top center',
            textfont=dict(color='orange', size=9),
            hovertemplate=f'<b>Breakeven: ${be:.2f}</b><extra></extra>'
        ))

    # Update layout
    fig.update_layout(
        title=dict(
            text=f"<b>P/L Diagram: {strategy_name}</b>",
            x=0.5,
            xanchor='center',
            font=dict(size=18)
        ),
        xaxis_title="<b>Stock Price at Expiration ($)</b>",
        yaxis_title="<b>Profit/Loss ($)</b>",
        hovermode='x unified',
        template='plotly_white',
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis=dict(
            gridcolor='lightgray',
            showgrid=True,
            tickformat='$,.0f'
        ),
        yaxis=dict(
            gridcolor='lightgray',
            showgrid=True,
            tickformat='$,.0f',
            zeroline=True,
            zerolinewidth=2,
            zerolinecolor='gray'
        )
    )

    return fig


def create_metrics_table(
    max_profit: float,
    max_loss: float,
    breakevens: List[float],
    current_price: float,
    net_debit_credit: float,
    risk_reward_ratio: float,
    current_pnl: float,
    greeks: Optional[dict] = None
) -> str:
    """
    Create formatted metrics table as HTML.

    Args:
        max_profit: Maximum profit
        max_loss: Maximum loss
        breakevens: List of breakeven prices
        current_price: Current stock price
        net_debit_credit: Net debit (positive) or credit (negative)
        risk_reward_ratio: Risk/reward ratio
        current_pnl: Current P/L at current price
        greeks: Optional dict with portfolio Greeks

    Returns:
        HTML string with formatted table
    """
    # Format breakevens
    if len(breakevens) == 0:
        breakeven_str = "None"
    elif len(breakevens) == 1:
        breakeven_str = f"${breakevens[0]:.2f}"
    else:
        breakeven_str = ", ".join([f"${be:.2f}" for be in breakevens])

    # Determine if debit or credit
    position_type = "Net Debit" if net_debit_credit > 0 else "Net Credit"
    position_value = abs(net_debit_credit)

    # Calculate return percentages
    if net_debit_credit != 0:
        return_if_max = (max_profit / abs(net_debit_credit)) * 100
    else:
        return_if_max = 0

    html = f"""
    <table style="width:100%; border-collapse: collapse; font-size: 14px;">
        <thead>
            <tr style="background-color: #f0f0f0;">
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Metric</th>
                <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">Value</th>
                <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Notes</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><b>Max Profit</b></td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd; color: green;">
                    <b>${max_profit:,.2f}</b>
                </td>
                <td style="padding: 8px; border: 1px solid #ddd;">Best case scenario</td>
            </tr>
            <tr style="background-color: #f9f9f9;">
                <td style="padding: 8px; border: 1px solid #ddd;"><b>Max Loss</b></td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd; color: red;">
                    <b>${abs(max_loss):,.2f}</b>
                </td>
                <td style="padding: 8px; border: 1px solid #ddd;">Worst case scenario</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><b>Breakeven(s)</b></td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">
                    <b>{breakeven_str}</b>
                </td>
                <td style="padding: 8px; border: 1px solid #ddd;">Where P/L = $0</td>
            </tr>
            <tr style="background-color: #f9f9f9;">
                <td style="padding: 8px; border: 1px solid #ddd;"><b>{position_type}</b></td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">
                    <b>${position_value:,.2f}</b>
                </td>
                <td style="padding: 8px; border: 1px solid #ddd;">Capital required</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><b>Risk/Reward Ratio</b></td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">
                    <b>{risk_reward_ratio:.2f}:1</b>
                </td>
                <td style="padding: 8px; border: 1px solid #ddd;">
                    {'Good' if risk_reward_ratio >= 1.5 else 'Moderate' if risk_reward_ratio >= 0.8 else 'Low'}
                </td>
            </tr>
            <tr style="background-color: #f9f9f9;">
                <td style="padding: 8px; border: 1px solid #ddd;"><b>Return if Max Profit</b></td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">
                    <b>{return_if_max:.1f}%</b>
                </td>
                <td style="padding: 8px; border: 1px solid #ddd;">ROI at max profit</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd;"><b>Current P/L</b></td>
                <td style="padding: 8px; text-align: right; border: 1px solid #ddd; color: {'green' if current_pnl >= 0 else 'red'};">
                    <b>${current_pnl:,.2f}</b>
                </td>
                <td style="padding: 8px; border: 1px solid #ddd;">At current price ${current_price:.2f}</td>
            </tr>
        </tbody>
    </table>
    """

    # Add Greeks if provided
    if greeks:
        html += f"""
        <br>
        <h4>Portfolio Greeks</h4>
        <table style="width:100%; border-collapse: collapse; font-size: 14px;">
            <thead>
                <tr style="background-color: #f0f0f0;">
                    <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Greek</th>
                    <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">Value</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Meaning</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><b>Delta</b></td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">
                        {greeks['portfolio_delta']:.2f}
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd;">
                        Directional exposure (±$1 stock move)
                    </td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 8px; border: 1px solid #ddd;"><b>Theta</b></td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">
                        {greeks['portfolio_theta']:.2f}
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd;">
                        Time decay per day
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><b>Vega</b></td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">
                        {greeks['portfolio_vega']:.2f}
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd;">
                        Sensitivity to 1% IV change
                    </td>
                </tr>
                <tr style="background-color: #f9f9f9;">
                    <td style="padding: 8px; border: 1px solid #ddd;"><b>Gamma</b></td>
                    <td style="padding: 8px; text-align: right; border: 1px solid #ddd;">
                        {greeks['portfolio_gamma']:.4f}
                    </td>
                    <td style="padding: 8px; border: 1px solid #ddd;">
                        Rate of Delta change
                    </td>
                </tr>
            </tbody>
        </table>
        """

    return html
