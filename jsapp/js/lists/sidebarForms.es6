import React from 'react';
import PropTypes from 'prop-types';
import reactMixin from 'react-mixin';
import autoBind from 'react-autobind';
import Reflux from 'reflux';
import { Link } from 'react-router';
import mixins from '../mixins';
import bem from '../bem';
import ui from '../ui';
import searches from '../searches';
import stores from '../stores';
import SearchCollectionList from '../components/searchcollectionlist';

import {
  parsePermissions,
  t,
  assign
} from '../utils';

class SidebarFormsList extends Reflux.Component {
  constructor(props) {
    super(props);
    var selectedCategories = {
      'Draft': false,
      'Deployed': false, 
      'Archived': false
    }
    this.state = {
      selectedCategories: selectedCategories,
      searchContext: searches.getSearchContext('forms', {
        filterParams: {
          assetType: 'asset_type:survey',
        },
        filterTags: 'asset_type:survey',
      })
    };
    this.store = stores.pageState;
    autoBind(this);
  }
  componentDidMount () {
    this.listenTo(this.searchStore, this.searchChanged);
    if (!this.isFormList())
      this.searchDefault();
  }
  componentWillReceiveProps () {
    this.listenTo(this.searchStore, this.searchChanged);
  }
  searchChanged (searchStoreState) {
    this.setState(searchStoreState);
  }
  renderMiniAssetRow (resource) {
    var active = '';
    if (resource.uid == this.currentAssetID())
      active = ' active';

    return (
        <bem.FormSidebar__item key={resource.uid} className={active}>
          <Link to={`/forms/${resource.uid}`} className={`form-sidebar__itemlink`}>
            <ui.SidebarAssetName {...resource} />
          </Link>
        </bem.FormSidebar__item>
      );
  }
  toggleCategory(c) {
    return function (e) {
    var selectedCategories = this.state.selectedCategories;
    selectedCategories[c] = !selectedCategories[c];
      this.setState({
        selectedCategories: selectedCategories,
      });
    }.bind(this)
  }
  render () {
    var s = this.state;
    var activeItems = 'defaultQueryCategorizedResultsLists';

    // sync sidebar with main list when it is not a search query, allows for deletes to update the sidebar as well
    // this is a temporary fix, a proper fix needs to update defaultQueryCategorizedResultsLists when deleting/archiving/cloning
    if (s.searchState === 'done' && 
        (s.searchString === false || s.searchString === "") &&
        s.searchResultsFor && 
        s.searchResultsFor.assetType === 'asset_type:survey')
      activeItems = 'searchResultsCategorizedResultsLists';

    if (s.searchState === 'loading' && s.searchString === false ) {
      return (
        <bem.Loading>
          <bem.Loading__inner>
            <i />
            {t('loading...')} 
          </bem.Loading__inner>
        </bem.Loading>
      );
    }

    return (
        <bem.FormSidebar>
        {
            <bem.FormSidebar__label className="all-projects">
                <a href="#/forms" className="form-sidebar__itemlink">
                    <i className="k-icon-projects" />
                    {t('All Projects')}
                </a>
            </bem.FormSidebar__label>
        }
        { 
          s.defaultQueryState === 'done' && 
          <bem.FormSidebar__label m={'active-projects'} className="is-edge">
            <i className="k-icon-projects" />
            {t('Active Projects')}
          </bem.FormSidebar__label>
        }
        {
          (() => {
            if (s.defaultQueryState === 'loading') {
              return (
                <bem.Loading>
                  <bem.Loading__inner>
                    <i />
                    {t('loading...')} 
                  </bem.Loading__inner>
                </bem.Loading>
              );
            } else if (s.defaultQueryState === 'done') {
              return ['Deployed', 'Draft', 'Archived' /*, 'Deleted'*/].map(
                (category) => {
                  var categoryVisible = this.state.selectedCategories[category];
                  if (s[activeItems][category].length < 1) {
                    categoryVisible = false;
                  }
                  return [
                    <bem.FormSidebar__label m={[category, categoryVisible ? 'visible' : 'collapsed']} 
                                            onClick={this.toggleCategory(category)}>
                      <i />
                      {t(category)}
                      <bem.FormSidebar__labelCount>
                        {s[activeItems][category].length}
                      </bem.FormSidebar__labelCount>
                    </bem.FormSidebar__label>,
                    <bem.FormSidebar__grouping m={[category, categoryVisible ? 'visible' : 'collapsed']}>
                      {
                        s[activeItems][category].map(this.renderMiniAssetRow)
                      }
                    </bem.FormSidebar__grouping>
                  ];
                }
              );
            }
          })()
        }
        {
            <bem.FormSidebar__label className="all-projects">
                <hr/>
                <a href="#/library" className="form-sidebar__itemlink">
                    <i className="k-icon-library" />
                    {t('Question Library')}
                </a>
            </bem.FormSidebar__label>
        }
        {
            <bem.FormSidebar__label className="all-projects">
                <a href="/admin" className="form-sidebar__itemlink" target="_blank">
                    <i className="k-icon-share" />
                    {t('User management')}
                </a>
            </bem.FormSidebar__label>
        }
        <bem.FormSidebar__label className="is-edge">
          <i className="k-icon-trash" />
          {t('Deleted')} (#)
        </bem.FormSidebar__label>
        
      </bem.FormSidebar>
    );
  }
};

SidebarFormsList.contextTypes = {
  router: PropTypes.object
};

reactMixin(SidebarFormsList.prototype, searches.common);
reactMixin(SidebarFormsList.prototype, Reflux.ListenerMixin);
reactMixin(SidebarFormsList.prototype, mixins.contextRouter);

export default SidebarFormsList;
