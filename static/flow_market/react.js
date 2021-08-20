console.log('react.js ran');

const html = htm.bind(React.createElement);
const App = (props) => {
  return html`<div>
    <div id="MANUAL_INPUT">
      <div
        className=" conditionalMarginBot cardWrapper d-flex align-items-center manual minWidth fixedHeightModified"
        id="MANUAL"
      >
        <div className="p-4 borderRadiusFix col shadow">
          <div className="row h-100 justify-content-center">
            <div className="col">
              <div
                className="h-100 text-center d-flex align-items-center flex-column justify-content-between"
              >
                <div className="mb-1 cardHeader w-100 text-align-right">
                  <div className="dropdown show">
                    <a
                      className="inputDropdown copyH5 btn btn-secondary dropdown-toggle"
                      href="#"
                      role="button"
                      data-toggle="dropdown"
                      aria-haspopup="true"
                      aria-expanded="false"
                    >
                      Manual Input
                    </a>
                    <div className="dropdown-menu">
                      <a
                        className="active dropdown-item manualInputDropdown"
                        onClick=${(event) => InputDropdown.handleClick(event)}
                        >Manual Input</a
                      >
                      <a
                        className="dropdown-item algorithmicInputDropdown"
                        onClick=${(event) => InputDropdown.handleClick(event)}
                        >Algorithmic Input</a
                      >
                    </div>
                  </div>
                </div>

                <form className="formPadding">
                  <div className="form-group row w-75">
                    <div
                      className="w-100 d-flex justify-content-between sliderWrapper"
                    >
                      <label className="mr-4" id="">Price</label>
                      <div
                        id="noUiPriceSlider"
                        className="noUiSlider"
                        style=${{minWidth: '200px'}}
                      ></div>
                    </div>
                  </div>
                  <div
                    className="noUiVolSliderWrapper form-group row mt-4 w-75"
                  >
                    <div
                      className="w-100 d-flex justify-content-between sliderWrapper"
                    >
                      <label className="mr-4" id="">Volume</label>
                      <div
                        id="noUiVolSlider"
                        className="noUiSlider"
                        style=${{minWidth: '200px'}}
                      ></div>
                    </div>
                  </div>
                  <div
                    className="noUiRateSliderWrapper form-group row mt-4 w-75"
                  >
                    <div
                      className="w-100 d-flex justify-content-between sliderWrapper"
                    >
                      <label className="mr-4" id="">Rate</label>
                      <div
                        id="noUiRateSlider"
                        className="noUiSlider"
                        style=${{minWidth: '200px'}}
                      ></div>
                    </div>
                  </div>
                </form>

                <div className="mt-2">
                  <button
                    type="button"
                    id="sendBid"
                    className="btn mr-3 btn-primary"
                    onClick=${new_buy}
                  >
                    Send Buy
                  </button>
                  <button
                    type="button"
                    id="sendAsk"
                    className="btn btn-danger"
                    onClick=${new_sell}
                  >
                    Send Sell
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>`;
};

ReactDOM.render(
  html`<${App} foo=${'bar'} />`,
  document.getElementById('reactInputSelectorTest')
);

/*
<div id="MANUAL_INPUT">
  <div
    className=" conditionalMarginBot cardWrapper d-flex align-items-center manual minWidth fixedHeightModified"
    id="MANUAL">
    <div className="p-4 borderRadiusFix col shadow">
      <div className="row h-100 justify-content-center">
        <div className="col">
          <div
            className="h-100 text-center d-flex align-items-center flex-column justify-content-between">
            <div className="mb-1 cardHeader w-100 text-align-right">
              <div className="dropdown show">
                <a className="inputDropdown copyH5 btn btn-secondary dropdown-toggle"
                  href="#" role="button" data-toggle="dropdown"
                  aria-haspopup="true" aria-expanded="false">
                  Manual Input
                </a>
                <div className="dropdown-menu">
                  <a className="active dropdown-item manualInputDropdown"
                    onClick="InputDropdown.handleClick(event)">Manual
                    Input</a>
                  <a className="dropdown-item algorithmicInputDropdown"
                    onClick="InputDropdown.handleClick(event)">Algorithmic
                    Input</a>
                </div>
              </div>
            </div>
            <form className="formPadding">
              <div className="form-group row w-75">
                <div
                  className="w-100 d-flex justify-content-between sliderWrapper">
                  <label className="mr-4" id="">Price</label>
                  <div id="noUiPriceSlider" className="noUiSlider"
                    style="min-width:200px;"></div>
                </div>
              </div>
              <div className="noUiVolSliderWrapper form-group row mt-4 w-75">
                <div
                  className="w-100 d-flex justify-content-between sliderWrapper">
                  <label className="mr-4" id="">Volume</label>
                  <div id="noUiVolSlider" className="noUiSlider"
                    style="min-width:200px;"></div>
                </div>
              </div>
              <div className="noUiRateSliderWrapper form-group row mt-4 w-75">
                <div
                  className="w-100 d-flex justify-content-between sliderWrapper">
                  <label className="mr-4" id="">Rate</label>
                  <div id="noUiRateSlider" className="noUiSlider"
                    style="min-width:200px;"></div>
                </div>
              </div>
            </form>
            <div className="mt-2">
              <button type="button" id="sendBid"
                className="btn mr-3 btn-primary" onClick="new_buy()">
                Send Buy
              </button>
              <button type="button" id="sendAsk" className="btn btn-danger"
                onClick="new_sell()">
                Send Sell
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<div id="ALGORITHMIC_INPUT" className="marginBottom  marginLeftModified">
  <div
    className="shadow d-flex align-items-center minWidth fixedAlgoInputHeight  cardWrapper"
    id="ALGORITHM">
    <div className="col p-4">
      <div className="row pt-2 h-100 justify-content-center">
        <div className="text-center d-flex flex-column justify-content-between">
          <div className="cardHeader w-100 text-align-right">
            <div className="dropdown show">
              <a className="mb-0 inputDropdown copyH5 btn btn-secondary dropdown-toggle"
                href="#" role="button" data-toggle="dropdown"
                aria-haspopup="true" aria-expanded="false">
                Algorithmic Input
              </a>
              <div className="dropdown-menu">
                <a className=" dropdown-item manualInputDropdown"
                  onClick="InputDropdown.handleClick(event)">Manual
                  Input</a>
                <a className="active dropdown-item algorithmicInputDropdown"
                  onClick="InputDropdown.handleClick(event)">Algorithmic
                  Input</a>
              </div>
            </div>
          </div>
          <div className="mb-4 noUiAlgoTimeSliderWrapper form-group row mt-4">
            <div className="d-flex justify-content-between sliderWrapper">
              <label className="mr-4" id="">Expiration Time</label>
              <div id="noUiAlgoTimeSlider" className="noUiSlider"
                style="min-width:200px;"></div>
            </div>
          </div>
          <div
            className="mb-4 noUiAlgoQuantitySliderWrapper form-group row mt-4">
            <div className="w-100 d-flex justify-content-between sliderWrapper">
              <label className="mr-4" id="">Units at a time</label>
              <div id="noUiAlgoQuantitySlider" className="noUiSlider"
                style="min-width:200px;"></div>
            </div>
          </div>
          <div className="mb-4 noUiAlgoPriceSliderWrapper form-group row mt-4">
            <div className="w-100 d-flex justify-content-between sliderWrapper">
              <label className="mr-4" id="">Price</label>
              <div id="noUiAlgoPriceSlider" className="noUiSlider"
                style="min-width:200px;"></div>
            </div>
          </div>
          <div className="mb-4 noUiAlgoVolSliderWrapper form-group row mt-4">
            <div className="d-flex w-100 justify-content-between sliderWrapper">
              <label className="mr-4" id="">Volume</label>
              <div id="noUiAlgoVolSlider" className="noUiSlider"
                style="min-width:200px;"></div>
            </div>
          </div>
          <div className="noUiAlgoRateSliderWrapper form-group row mt-4">
            <div className="w-100 d-flex justify-content-between sliderWrapper">
              <label className="mr-4" id="">Rate</label>
              <div id="noUiAlgoRateSlider" className="noUiSlider"
                style="min-width:200px;"></div>
            </div>
          </div>
          <div>
            <div className="mt-3">
              <button type="button" id="algo-sendBid"
                className="btn mr-3 btn-primary" onClick="new_buy_algo()">
                Send Buy
              </button>
              <button type="button" id="algo-sendAsk" className="btn btn-danger"
                onClick="new_sell_algo()">
                Send Sell
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
*/
