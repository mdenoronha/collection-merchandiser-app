var actions = AppBridge.actions;
var ResourcePicker = actions.ResourcePicker;
var Button = actions.Button;
var ButtonGroup = actions.ButtonGroup;
var Redirect = actions.Redirect;
var TitleBar = actions.TitleBar;
var Loading = actions.Loading;

// Init redirect
const redirect = Redirect.create(app);
// Init loading
const loading = Loading.create(app);

// Secondary buttons
const homeButton = Button.create(app, {label: 'Home'});
const contactButton = Button.create(app, {label: 'Contact'});
const instructionsButton = Button.create(app, {label: 'Instructions'});
const privacyButton = Button.create(app, {label: 'Privacy Policy'});
const automationsButton = Button.create(app, {label: 'Automations'});
const save = Button.create(app, {label: 'Save'});

const groupButton = ButtonGroup.create(app, {label: 'Navigation', buttons: [homeButton, contactButton,automationsButton, instructionsButton, privacyButton]});
// Secondary buttons actions
const viewContact = contactButton.subscribe(Button.Action.CLICK, data => {
  redirect.dispatch(Redirect.Action.APP, '/contact');
});
const homeContact = homeButton.subscribe(Button.Action.CLICK, data => {
  redirect.dispatch(Redirect.Action.APP, homeLink);
});
const viewInstructions = instructionsButton.subscribe(Button.Action.CLICK, data => {
  redirect.dispatch(Redirect.Action.APP, '/instructions');
});
const viewPrivacy = privacyButton.subscribe(Button.Action.CLICK, data => {
  redirect.dispatch(Redirect.Action.APP, '/privacy-policy');
});
const viewAutomations = automationsButton.subscribe(Button.Action.CLICK, data => {
  redirect.dispatch(Redirect.Action.APP, '/automations');
});
const rulesCollectionPicker = ResourcePicker.create(app, {
  resourceType: ResourcePicker.ResourceType.Collection,
  options: {
    selectMultiple: true,
    showHidden: true
  }
});


