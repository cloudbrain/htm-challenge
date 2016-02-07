import request from './request';
import logger from './logger';
import dom from './dom';
// import hello from 'hellojs'; //Modifies objects to have id parameter?
// import hello from 'hellojs'; //After es version of module is created
//Private object containing clientIds
let clientIds = {};

class ProviderAuth {
	constructor(actionData) {
		this.app = actionData.app ? actionData.app : null;
		this.redirectUri = actionData.redirectUri ? actionData.redirectUri : 'redirect.html';
		this.provider = actionData.provider ? actionData.provider : null;
	}
	/** Load hellojs library script into DOM
	 */
	loadHello() {
		//Load hellojs script
		//TODO: Replace this with es6ified version
		if (typeof window != 'undefined' && !window.hello) {
			return dom.asyncLoadJs('https://s3.amazonaws.com/kyper-cdn/js/hello.js');
		} else {
			return Promise.reject();
		}
	}
	helloLoginListener() {
		//Login Listener
		window.hello.on('auth.login', (auth) => {
			logger.info({description: 'User logged in to google.', func: 'loadHello', obj: 'Google'});
			// Call user information, for the given network
			window.hello(auth.network).api('/me').then(function(r) {
				// Inject it into the container
				//TODO:Send account informaiton to server
				var userData = r;
				userData.provider = auth.network;
				//Login or Signup endpoint
				return request.post(this.endpoint + '/provider', userData)
					.then((response) => {
						logger.log({description: 'Provider request successful.',  response: response, func: 'signup', obj: 'GoogleUtil'});
						return response;
					})
					['catch']((errRes) => {
						logger.error({description: 'Error requesting login.', error: errRes, func: 'signup', obj: 'Matter'});
						return Promise.reject(errRes);
					});
			});
		});
	}
	/** Initialize hellojs library and request app providers
	 */
	initHello() {
		return this.loadHello().then(() => {
			return request.get(`${this.app.endpoint}/providers`)
			.then((response) => {
				logger.log({
					description: 'Provider request successful.',  response: response,
					func: 'initHello', obj: 'ProviderAuth'
				});
				let provider = response[this.provider];
				if (!provider) {
					logger.error({
						description: 'Provider is not setup.\n' +
						'Visit build.kyper.io to enter your client id for ' + this.provider,
						provider: this.provider, clientIds: clientIds,
						func: 'login', obj: 'ProviderAuth'
					});
					return Promise.reject({message: 'Provider is not setup.'});
				}
				logger.log({
					description: 'Providers config built', providersConfig: response,
					func: 'initHello', obj: 'ProviderAuth'
				});
				return window.hello.init(response, {redirect_uri: 'redirect.html'});
			}, (errRes) => {
				logger.error({
					description: 'Error loading hellojs.', error: errRes,
					func: 'initHello', obj: 'ProviderAuth'
				});
				return Promise.reject({message: 'Error requesting application third party providers.'});
			})
			['catch']((errRes) => {
				logger.error({
					description: 'Error loading hellojs.', error: errRes, func: 'initHello', obj: 'ProviderAuth'
				});
				return Promise.reject({message: 'Error loading third party login capability.'});
			});
		});
	}
  /** External provider login
   * @example
   * //Login to account that was started through external account signup (Google, Facebook, Github)
   * ProviderAuth('google').login().then(function(loginRes){
   * 		console.log('Successful login:', loginRes)
   * }, function(err){
   * 		console.error('Error with provider login:', err);
   * });
   */
	login() {
		return this.initHello().then(() => {
			return window.hello.login(this.provider);
		}, (err) => {
			logger.error({description: 'Error initalizing hellojs.', error: err, func: 'login', obj: 'Matter'});
			return Promise.reject({message: 'Error with third party login.'});
		});
	}
	/** Signup using external provider account (Google, Facebook, Github)
   * @example
   * //Signup using external account (Google, Facebook, Github)
   * ProviderAuth('google').signup().then(function(signupRes){
   * 		console.log('Successful signup:', signupRes)
   * }, function(err){
   * 		console.error('Error with provider signup:', err);
   * });
	 */
	signup() {
		//TODO: send info to server
		return this.login();
	}
}
export default ProviderAuth;
