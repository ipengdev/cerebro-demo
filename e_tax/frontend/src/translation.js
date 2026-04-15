const translations = {
  en: {},
  fr: {
    // Navigation
    'Dashboard': 'Tableau de bord',
    'Enterprise Declarations': 'Déclarations d\'entreprise',
    'VAT Returns': 'Déclarations de TVA',
    'Personal Income Tax': 'Impôt sur le revenu des personnes physiques',
    'Customs Declarations': 'Déclarations douanières',
    'Excise Duty Returns': 'Déclarations de droits d\'accise',
    'Taxpayers': 'Contribuables',
    'Settings': 'Paramètres',

    // Dashboard
    'Total Revenue': 'Revenu total',
    'Active Taxpayers': 'Contribuables actifs',
    'Pending Reviews': 'Examens en attente',
    'Filed This Month': 'Déposé ce mois-ci',
    'Revenue Overview': 'Aperçu des revenus',
    'Recent Filings': 'Dépôts récents',
    'Monthly Filing Trends': 'Tendances mensuelles de dépôt',
    'Revenue by Tax Type': 'Revenus par type d\'impôt',

    // Status
    'Draft': 'Brouillon',
    'Submitted': 'Soumis',
    'Under Review': 'En cours d\'examen',
    'Approved': 'Approuvé',
    'Rejected': 'Rejeté',
    'Active': 'Actif',
    'Suspended': 'Suspendu',
    'Deregistered': 'Radié',

    // Tax Types
    'Income Tax': 'Impôt sur le revenu',
    'Social Tax': 'Taxe sociale',
    'VAT': 'TVA',
    'Excise Duty': 'Droits d\'accise',
    'Customs Duty': 'Droits de douane',
    'Unemployment Insurance': 'Assurance chômage',
    'Pension Fund': 'Fonds de pension',

    // Excise Types
    'Alcohol Excise': 'Accise sur l\'alcool',
    'Tobacco Excise': 'Accise sur le tabac',
    'Fuel Excise': 'Accise sur le carburant',
    'Packaging Excise': 'Accise sur l\'emballage',

    // Customs
    'Import': 'Importation',
    'Export': 'Exportation',
    'Transit': 'Transit',
    'Re-export': 'Réexportation',
    'Temporary Import': 'Importation temporaire',

    // Form Labels
    'Taxpayer Name': 'Nom du contribuable',
    'Tax Identification Number (TIN)': 'Numéro d\'identification fiscale (NIF)',
    'Fiscal Year': 'Année fiscale',
    'Filing Date': 'Date de dépôt',
    'Due Date': 'Date d\'échéance',
    'Declaration Period': 'Période de déclaration',
    'Monthly': 'Mensuel',
    'Quarterly': 'Trimestriel',
    'Annually': 'Annuel',
    'Gross Revenue': 'Chiffre d\'affaires brut',
    'Allowable Deductions': 'Déductions admissibles',
    'Taxable Income': 'Revenu imposable',
    'Total Tax Liability': 'Impôt total dû',
    'Balance Due': 'Solde dû',
    'Total Sales': 'Ventes totales',
    'Exempt Sales': 'Ventes exonérées',
    'Zero-Rated Sales': 'Ventes à taux zéro',
    'Total Purchases': 'Achats totaux',
    'VAT Payable': 'TVA à payer',
    'VAT Refund Due': 'Remboursement de TVA dû',
    'Employment Income': 'Revenus d\'emploi',
    'Business Income': 'Revenus d\'activité',
    'Rental Income': 'Revenus locatifs',
    'Investment Income': 'Revenus de placement',
    'Tax Payable': 'Impôt à payer',
    'Tax Refund Due': 'Remboursement d\'impôt dû',

    // Actions
    'Create New': 'Créer nouveau',
    'Submit': 'Soumettre',
    'Approve': 'Approuver',
    'Reject': 'Rejeter',
    'Cancel': 'Annuler',
    'Save': 'Sauvegarder',
    'View All': 'Voir tout',
    'Download': 'Télécharger',
    'Print': 'Imprimer',
    'Search': 'Rechercher',
    'Filter': 'Filtrer',

    // General
    'e-Tax': 'e-Tax',
    'Electronic Tax Filing System': 'Système de déclaration fiscale électronique',
    'Tax and Customs Board': 'Direction des impôts et des douanes',
    'Welcome back': 'Bienvenue',
    'Overview of your tax administration': 'Aperçu de votre administration fiscale',
    'Individual': 'Particulier',
    'Enterprise': 'Entreprise',
    'Government Entity': 'Entité gouvernementale',
    'Non-Profit': 'Organisation à but non lucratif',
    'No data available': 'Aucune donnée disponible',
    'Loading...': 'Chargement...',
    'Enterprises': 'Entreprises',
    'Individuals': 'Particuliers',
    'Language': 'Langue',
    'English': 'Anglais',
    'French': 'Français',

    // Demo Data
    'Demo Data': 'Données de démonstration',
    'Generate sample taxpayers, declarations, and demo users for testing. Demo users: company@etax.demo, person@etax.demo, agent@etax.demo (password: Demo@1234)': 'Générer des contribuables, déclarations et utilisateurs fictifs pour les tests. Utilisateurs : company@etax.demo, person@etax.demo, agent@etax.demo (mot de passe : Demo@1234)',
    'Demo data is active': 'Données de démonstration actives',
    'No demo data loaded': 'Aucune donnée de démonstration chargée',
    'taxpayers': 'contribuables',
    'Create Demo Data': 'Créer les données de démo',
    'Clear Demo Data': 'Supprimer les données de démo',
    'Creating...': 'Création...',
    'Clearing...': 'Suppression...',
    'Demo data created successfully! 3 users, 5 taxpayers, and sample declarations added.': 'Données de démo créées avec succès ! 3 utilisateurs, 5 contribuables et des déclarations ajoutés.',
    'All demo data has been cleared.': 'Toutes les données de démonstration ont été supprimées.',
    'Failed to create demo data': 'Échec de la création des données de démo',
    'Failed to clear demo data': 'Échec de la suppression des données de démo',
    'Are you sure you want to remove all demo data? This will delete demo users, taxpayers, and all their declarations.': 'Êtes-vous sûr de vouloir supprimer toutes les données de démo ? Cela supprimera les utilisateurs, contribuables et toutes leurs déclarations.',
  },
}

let currentLang = localStorage.getItem('etax_lang') || 'en'

const translationPlugin = {
  install(app) {
    app.config.globalProperties.__ = function (text) {
      if (currentLang === 'en') return text
      return translations[currentLang]?.[text] || text
    }
    app.provide('__', app.config.globalProperties.__)
    app.provide('setLang', (lang) => {
      currentLang = lang
      localStorage.setItem('etax_lang', lang)
      window.location.reload()
    })
    app.provide('getLang', () => currentLang)
  },
}

export default translationPlugin

export function __(text) {
  if (currentLang === 'en') return text
  return translations[currentLang]?.[text] || text
}
