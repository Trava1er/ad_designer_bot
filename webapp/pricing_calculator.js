// Pricing Calculator Module
// Динамический расчёт стоимости с учётом тарифов и дополнительных услуг

class PricingCalculator {
    constructor(config) {
        this.config = config;
        this.selectedTariff = null;
        this.selectedCurrency = 'RUB';
        this.additionalServices = [];
    }

    // Установить тариф
    setTariff(tariffId) {
        this.selectedTariff = tariffId;
    }

    // Установить валюту
    setCurrency(currency) {
        this.selectedCurrency = currency;
    }

    // Проверить, включена ли услуга в тариф
    isIncludedInTariff(serviceId) {
        if (!this.selectedTariff) return false;
        const service = this.config.additional_services[serviceId];
        return service && service.included_in.includes(this.selectedTariff);
    }

    // Получить цену услуги
    getServicePrice(serviceId) {
        const service = this.config.additional_services[serviceId];
        if (!service) return 0;
        
        // Если включено в тариф - бесплатно
        if (this.isIncludedInTariff(serviceId)) {
            return 0;
        }
        
        return service.prices[this.selectedCurrency] || 0;
    }

    // Получить базовую цену тарифа
    getTariffPrice() {
        if (!this.selectedTariff) return 0;
        const tariff = this.config.tariffs[this.selectedTariff];
        return tariff ? tariff.prices[this.selectedCurrency] : 0;
    }

    // Рассчитать итоговую стоимость
    calculateTotal() {
        let total = this.getTariffPrice();
        
        this.additionalServices.forEach(serviceId => {
            total += this.getServicePrice(serviceId);
        });
        
        return total;
    }

    // Добавить дополнительную услугу
    addService(serviceId) {
        if (!this.additionalServices.includes(serviceId)) {
            this.additionalServices.push(serviceId);
        }
    }

    // Удалить дополнительную услугу
    removeService(serviceId) {
        this.additionalServices = this.additionalServices.filter(id => id !== serviceId);
    }

    // Получить подсказку для пользователя
    getServiceHint(serviceId, lang = 'ru') {
        if (this.isIncludedInTariff(serviceId)) {
            const hints = {
                'ru': '✅ Входит в ваш тариф бесплатно',
                'en': '✅ Included in your plan for free',
                'zh-tw': '✅ 免費包含在您的方案中'
            };
            return hints[lang] || hints['ru'];
        }
        
        // Проверить, в какие тарифы входит
        const service = this.config.additional_services[serviceId];
        if (service && service.included_in.length > 0) {
            const includedInNames = service.included_in.map(tariffId => {
                return this.config.tariffs[tariffId].name[lang];
            }).join(', ');
            
            const hints = {
                'ru': `💡 Входит бесплатно в: ${includedInNames}`,
                'en': `💡 Free in: ${includedInNames}`,
                'zh-tw': `💡 免費包含於: ${includedInNames}`
            };
            return hints[lang] || hints['ru'];
        }
        
        return '';
    }

    // Форматировать цену с валютой
    formatPrice(amount) {
        const symbol = this.config.currency_symbols[this.selectedCurrency];
        return `${amount} ${symbol}`;
    }

    // Получить детали заказа
    getOrderDetails(lang = 'ru') {
        const details = {
            tariff: this.selectedTariff,
            tariffName: this.config.tariffs[this.selectedTariff]?.name[lang],
            tariffPrice: this.getTariffPrice(),
            services: [],
            total: 0
        };

        this.additionalServices.forEach(serviceId => {
            const service = this.config.additional_services[serviceId];
            const price = this.getServicePrice(serviceId);
            const isIncluded = this.isIncludedInTariff(serviceId);
            
            details.services.push({
                id: serviceId,
                name: service.name[lang],
                price: price,
                isIncluded: isIncluded,
                icon: service.icon
            });
        });

        details.total = this.calculateTotal();
        return details;
    }
}

// Export для использования
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PricingCalculator;
}
