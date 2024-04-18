(function($) {

	"use strict";


  // Form
	var contactForm = function() {
		if ($('#contactForm').length > 0 ) {
			$( "#contactForm" ).validate( {
				rules: {
					email: {
						required: true,
						email: true
					},
					password: {
						required: true,
						password: true
					}
				},
				messages: {
					email: "Veuillez saisir une adresse e-mail valide !",
					password: "Veuillez saisir votre mot de passe !"
				},
			});
		}
	};
	contactForm();

})(jQuery);
