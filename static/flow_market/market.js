import './color.js';
import {html,PolymerElement} from '/static/otree-redwood/node_modules/@polymer/polymer/polymer-element.js';
import '/static/otree-redwood/node_modules/@polymer/polymer/lib/elements/dom-repeat.js';

export class Market extends PolymerElement {
    static get template() {
        return html `
            <div class="layout vertical center">
                <label for="direction">Buy or Sell</label>
                <select id="direction" name="direection">
                    <option value="buy">Buy</option>
                    <option value="sell">Sell</option>
                </select>
                <br><br>

                <label for="max_q">Max Quantity</label>
                <input id="max_q" type="number"></input>
                <br><br>

                <label for="max_r">Max Rate</label>
                <input id="max_r" type="number"></input>
                <br><br>

                <label for="p_min">P Min</label>
                <input id="p_min" type="number"></input>
                <br><br>

                <label for="p_max">P Max</label>
                <input id="p_max" type="number"></input>
                <br><br>

                <button id="btn" on-click="_new_order">Send Order</button>
            </div>
        
        `
    }

    static get properties() {
        return {
            liveSend: {
                type: String
            }
        }
    }

    ready() {
        super.ready();
        
    }

    _new_order(){
        let direction = this.shadowRoot.querySelector('#direction').value;
        let max_q = parseFloat(this.shadowRoot.querySelector('#max_q').value);
        let max_r = parseFloat(this.shadowRoot.querySelector('#max_r').value);
        let p_min = parseFloat(this.shadowRoot.querySelector('#p_min').value);
        let p_max = parseFloat(this.shadowRoot.querySelector('#p_max').value);

        liveSend({
            'direction': direction,
            'max_quantity': max_q,
            'max_rate': max_r,
            'p_min':p_min,
            'p_max':p_max,
            'status': 'active',
            'timestamp':performance.now()
        });
    }

    liveRecv(data){
        console.log(data);

    }


}

window.customElements.define('leeps-market', Market);