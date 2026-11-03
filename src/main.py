from elyx import strings # type: ignore

from hook_utils import find_class
from base_plugin import BasePlugin
from client_utils import get_last_fragment
from ui.settings import Divider, EditText, Header, Input, Text, Switch, Selector, Custom
from ui.bulletin import BulletinHelper

from .now_playing_tracker import NowPlayingTracker

from .utils.global_utils import logcat
from .utils.keyboard_utils import reset_keyboard_state

from .ui.settings.platforms.platforms_cell_setting import PlatformsCellSettingFactory
from .ui.settings.preview.card_type_cell import CardTypeCellSettingFactory
from .ui.settings.stream.stream_settings_fragment import StreamSettingsFragment

from .hooks.adapter_get_title_hook import AdapterGetTitleHook
from .hooks.emoji_view_constructor_hook import EmojiViewConstructorHook
from .hooks.set_allow_hook import SetAllowHook
from .hooks.set_blurred_background_drawable_factory import SetBlurredBackgroundDrawableFactoryHook
from .hooks.on_open_hook import OnOpenHook
from .hooks.on_page_selected_hook import OnPageSelectedHook
from .hooks.save_new_page_hook import SaveNewPageHook
from .hooks.set_emoji_button_icon_hook import SetEmojiButtonIconHook

from java.lang import Integer, Boolean # type: ignore

from org.telegram.messenger import ApplicationLoader, AndroidUtilities # type: ignore
from org.telegram.ui.Components import UItem # type: ignore
from org.telegram.ui.Components.blur3 import BlurredBackgroundDrawableViewFactory # type: ignore


def find_constructor_exact(clazz, *params):
    try:
        ctor = clazz.getDeclaredConstructor(*params)
        ctor.setAccessible(True)
        return ctor
    except:
        return None


def find_method_exact(clazz, name, *params):
    try:
        m = clazz.getDeclaredMethod(name, *params)
        m.setAccessible(True)
        return m
    except Exception as e:
        logcat(f'Failed to find method: {e}')
        return None


class ReSwagaPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self._now_playing_tracker = NowPlayingTracker.get_instance()
        self.hooks = []

        # a = ApplicationLoader.applicationContext.getPackageName()
        # if str(a) not in ('com.exteragram.messenger', 'com.radolyn.ayugram'):
        #     raise TypeError('otkazano xDDDDDDDDD')

    def on_plugin_load(self):
        self.platforms_cell = PlatformsCellSettingFactory.new_java_instance()
        UItem.UItemFactory.setup(self.platforms_cell)

        self.card_type_cell = CardTypeCellSettingFactory.new_java_instance()
        UItem.UItemFactory.setup(self.card_type_cell)
        
        self._now_playing_tracker.try_start_tracker()
        self._setup_hooks()
        # add_swag_pills()

    def on_plugin_unload(self):
        self._now_playing_tracker.stop_tracker()
        # remove_swag_pills()

        reset_keyboard_state()
        self._unhook_all()

    def _unhook_all(self):
        for unhook in self.hooks:
            if unhook is None:
                continue
            try:
                self.unhook_method(unhook)
            except Exception as e:
                logcat(f'Failed to unhook: {e}')

        self.hooks.clear()

    def create_settings(self):
        return [
            Header(strings["ui_settings_platforms_header"]),
            Custom(factory=self.platforms_cell),

            Divider(),

            Header(strings["ui_settings_card_header"]),
            Custom(factory=self.card_type_cell),
            Text(
                text=strings["ui_settings_card_customization"],
                link_alias='additionalCustomization',
                icon='msg_palette',
                create_sub_fragment=self._create_additional_customization_settings
            ),

            # Divider(),
            #
            # Header(strings["ui_settings_customization_header"]),
            # Switch(
            #     key='vertical_keyboard',
            #     text=strings['ui_settings_customization_vertical_keyboard'],
            #     default=True,
            # ),

            Divider(),

            Header(strings["ui_settings_stream_header"]),
            Text(
                text=strings['ui_settings_stream_settings'],
                link_alias='streamSettings',
                icon='msg_download_settings',
                on_click=lambda _: get_last_fragment().presentFragment(StreamSettingsFragment.new_java_instance())
            ),

            Divider(),

            Header(strings['ui_settings_donate']),
            Text(
                text=strings['ui_settings_donate_crypto'],
                accent=True,
                link_alias='donateCrypto',
                icon='outline_gram_24',
                on_click=lambda _: AndroidUtilities.addToClipboard('UQBVxjueXqAEpALX_b0yr-ytXN26LOTpSBn26b9VRHKrmm5F')
            ),
            # Text(
            #     text=strings['ui_settings_donate_card'],
            #     accent=True,
            #     link_alias='donateCard',
            #     icon='msg_palette',
            #     on_click=lambda _: AndroidUtilities.addToClipboard()
            # ),
        ]

    def _create_additional_customization_settings(self) -> list:
        return [
            Selector(
                key='card_background_type',
                text=strings['ui_settings_card_customization_background_type'],
                link_alias='cardBackgroundType',
                icon='msg_photos',
                default=0,
                items=[
                    strings['settings_background_type_track_cover'],
                    strings['settings_background_type_accent_color']
                ]
            ),

            Selector(
                key='card_font',
                text=strings['ui_settings_card_customization_font'],
                link_alias='cardFont',
                icon='msg_photo_text_regular',
                default=0,
                items=[
                    'Onest',
                    'Circular',
                    'NotoSansJP',
                    'YSMusic',
                    'YSText'
                ]
            ),

            Switch(
                key='link_to_other_platforms',
                text=strings['ui_settings_card_customization_link_to_other_platforms'],
                subtext=strings['ui_settings_card_customization_link_to_other_platforms_subtext'],
                link_alias='linkToOtherPlatforms',
                icon='msg_language',
                default=True,
            )
        ]

    def _setup_hooks(self):
        try:
            emoji_view = find_class("org.telegram.ui.Components.EmojiView").getClass()
            if not emoji_view: return

            # base_fragment = find_class("org.telegram.ui.ActionBar.BaseFragment").getClass()
            # resources_provider = find_class("org.telegram.ui.ActionBar.Theme$ResourcesProvider").getClass()
            # chat_full = find_class("org.telegram.tgnet.TLRPC$ChatFull").getClass()
            # context = find_class("android.content.Context").getClass()
            # view_group = find_class("android.view.ViewGroup").getClass()

            # ctor = find_constructor_exact(
            #     emoji_view,
            #     base_fragment, # fragment
            #     Boolean.TYPE, # needAnimatedEmoji
            #     Boolean.TYPE, # needStickers
            #     Boolean.TYPE, # needGif
            #     context, # context
            #     Boolean.TYPE, # needSearch
            #     chat_full, # chatFull
            #     view_group, # parentView
            #     Boolean.TYPE, # shouldDrawBackground
            #     resources_provider, # resourcesProvider
            #     Boolean.TYPE, # frozenAtStart
            #     Boolean.TYPE # glassDesign
            # )
            #
            # if ctor is None:
            #     logcat("Failed to find EmojiView constructor")
            #     return

            self.hooks.append(self.hook_all_constructors(emoji_view, EmojiViewConstructorHook()))

            set_allow = find_method_exact(emoji_view, "setAllow", Boolean.TYPE, Boolean.TYPE, Boolean.TYPE, Boolean.TYPE)
            if set_allow: self.hooks.append(self.hook_method(set_allow, SetAllowHook()))

            on_open = find_method_exact(emoji_view, "onOpen", Boolean.TYPE, Boolean.TYPE)
            if on_open: self.hooks.append(self.hook_method(on_open, OnOpenHook()))

            save_new_page = find_method_exact(emoji_view, "saveNewPage")
            if save_new_page: self.hooks.append(self.hook_method(save_new_page, SaveNewPageHook()))

            adapter_class = find_class("org.telegram.ui.Components.EmojiView$EmojiPagesAdapter").getClass()
            if adapter_class:
                get_title = find_method_exact(adapter_class, "getPageTitle", Integer.TYPE)
                if get_title: self.hooks.append(self.hook_method(get_title, AdapterGetTitleHook()))

            set_blurred_background_drawable_factory = find_method_exact(emoji_view, "setBlurredBackgroundDrawableFactory", BlurredBackgroundDrawableViewFactory.getClass())
            if set_blurred_background_drawable_factory: self.hooks.append(self.hook_method(set_blurred_background_drawable_factory, SetBlurredBackgroundDrawableFactoryHook()))

            view_pager = find_class("androidx.viewpager.widget.ViewPager").getClass()
            if view_pager:
                set_current_item = find_method_exact(view_pager, "dispatchOnPageSelected", Integer.TYPE)
                if set_current_item: self.hooks.append(self.hook_method(set_current_item, OnPageSelectedHook()))

            chat_activity_enter_view = find_class("org.telegram.ui.Components.ChatActivityEnterView").getClass()
            if chat_activity_enter_view: 
                set_emoji_button_icon = find_method_exact(chat_activity_enter_view, "setEmojiButtonImage", Boolean.TYPE, Boolean.TYPE)
                if set_emoji_button_icon: self.hooks.append(self.hook_method(set_emoji_button_icon, SetEmojiButtonIconHook()))
        except Exception as e:
            logcat(f"Setup error: {e}")
