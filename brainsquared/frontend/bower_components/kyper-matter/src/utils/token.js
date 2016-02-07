import config from '../config';
import logger from './logger';
import storage from './envStorage';
import jwtDecode from 'jwt-decode';
import _ from 'lodash';

let token = {
	/** Get string value of token
	 * @return {String}
	 * @example
	 * console.log('String value of current token', token.string);
	 */
	get string() {
		return storage.getItem(config.tokenName);
	},
	/** Get decoded data within token (unencrypted data only)
	 * @return {Object}
	 * @example
	 * console.log('Data of current token:', token.data);
	 */
	get data() {
		if (storage.getItem(config.tokenDataName)) {
			return storage.getItem(config.tokenDataName);
		} else {
			return decodeToken(this.string);
		}
	},
	/** Set token data
	 */
	set data(tokenData) {
		if (_.isString(tokenData)) {
			let tokenStr = tokenData;
			tokenData = decodeToken(tokenStr);
			logger.info({
				description: 'Token data was set as string. Decoding token.',
				token: tokenStr, tokenData: tokenData, func: 'data', obj: 'token'
			});
		} else {
			logger.log({
				description: 'Token data was set.', data: tokenData,
				func: 'data', obj: 'token'
			});
			storage.setItem(config.tokenDataName, tokenData);
		}
	},
	/** Set token value as a string
	 */
	set string(tokenData) {
		let tokenStr;
		//Handle object being passed
		if (!_.isString(tokenData)) {
			//Token is included in object
			logger.log({
				description: 'Token data is not string.',
				token: tokenData, func: 'string', obj: 'token'
			});
			if (_.isObject(tokenData) && _.has(tokenData, 'token')) {
				tokenStr = tokenData.token;
			} else {
				//Input is either not an string or object that contains nessesary info
				logger.error({
					description: 'Invalid value set to token.',
					token: tokenData, func: 'string', obj: 'token'
				});
				return;
			}
		} else {
			tokenStr = tokenData;
		}
		logger.log({
			description: 'Token was set.', token: tokenData,
			tokenStr: tokenStr, func: 'string', obj: 'token'
		});
		storage.setItem(config.tokenName, tokenStr);
		this.data = jwtDecode(tokenStr);
	},
	/** Save token data
	 */
	save(tokenStr) {
		this.string = tokenStr;
	},
	/** Delete token data
	 */
	delete() {
		//Remove string token
		storage.removeItem(config.tokenName);
		//Remove user data
		storage.removeItem(config.tokenDataName);
		logger.log({
			description: 'Token was removed.',
			func: 'delete', obj: 'token'
		});
	}
};

export default token;
/** Safley decode a JWT string
 * @private
 * @return {Object}
 */
function decodeToken(tokenStr) {
	let tokenData;
	if (tokenStr && tokenStr != '') {
		try {
			tokenData = jwtDecode(tokenStr);
		} catch (err) {
			logger.error({
				description: 'Error decoding token.', data: tokenData,
				error: err, func: 'decodeToken', file: 'token'
			});
			throw new Error('Invalid token string.');
		}
	}
	return tokenData;
}
